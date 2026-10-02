"""Offline, deterministic tests of episodic-cache request ownership.

Can also run without project dependencies:
    python -m unittest discover -s tests -p test_episodic_memory.py -v
"""
import asyncio
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch


def load_provider():
    """Load only this provider; scoped stubs never leak to other test modules."""
    logging_stub = ModuleType("addons.logging")
    logging_stub.get_logger = Mock(return_value=Mock())
    function_stub = ModuleType("function")
    function_stub.func = SimpleNamespace(report_error=AsyncMock())
    path = Path(__file__).resolve().parents[1] / "llm/memory/episodic.py"
    spec = importlib.util.spec_from_file_location("_episodic_under_test", path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {
        "discord": ModuleType("discord"),
        "addons.logging": logging_stub,
        "function": function_stub,
    }):
        spec.loader.exec_module(module)
    return module.EpisodicMemoryProvider, function_stub.func.report_error


class ControlledStore:
    def __init__(self):
        self.calls = asyncio.Queue()

    async def search_memories_by_vector(self, **kwargs):
        result = asyncio.get_running_loop().create_future()
        self.calls.put_nowait((kwargs, result))
        return await result


class EpisodicMemoryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        provider_class, self.report_error = load_provider()
        self.store = ControlledStore()
        self.provider = provider_class(SimpleNamespace(
            vector_manager=SimpleNamespace(store=self.store)
        ))
        self.message = SimpleNamespace(
            content="remember our previous project discussion",
            channel=SimpleNamespace(id=42),
        )
        self.key = ("42", self.message.content)
        self.tasks = []

    async def asyncTearDown(self):
        for task in self.tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

    def start_get(self, message=None):
        task = asyncio.create_task(self.provider.get(message or self.message))
        self.tasks.append(task)
        return task

    async def next_search(self):
        _, result = await asyncio.wait_for(self.store.calls.get(), timeout=1)
        return result

    @staticmethod
    def fragments(text):
        return [SimpleNamespace(content=text, metadata={})]

    async def test_invalidation_discards_inflight_result(self):
        old = self.start_get()
        result = await self.next_search()
        await self.provider.invalidate("42")
        result.set_result(self.fragments("obsolete memory"))
        self.assertIsNone(await old)
        self.assertNotIn(self.key, self.provider._cache)
        self.assertNotIn(self.key, self.provider._pending_queries)

    async def test_old_search_cannot_remove_replacement_or_release_its_waiter(self):
        old = self.start_get()
        old_result = await self.next_search()
        await self.provider.invalidate("42")
        new = self.start_get()
        new_result = await self.next_search()
        replacement_event = self.provider._pending_queries[self.key]
        waiter = self.start_get()
        await asyncio.sleep(0)  # Let the follower wait on the replacement event.
        old_result.set_result(self.fragments("obsolete memory"))
        self.assertIsNone(await old)
        self.assertIs(self.provider._pending_queries[self.key], replacement_event)
        self.assertFalse(replacement_event.is_set())
        self.assertFalse(waiter.done())
        new_result.set_result(self.fragments("fresh memory"))
        fresh = await new
        self.assertIn("fresh memory", fresh)
        self.assertEqual(await waiter, fresh)
        self.assertTrue(self.store.calls.empty())
        self.assertNotIn(self.key, self.provider._pending_queries)

    async def test_old_search_cannot_overwrite_completed_replacement(self):
        old = self.start_get()
        old_result = await self.next_search()
        await self.provider.invalidate("42")
        new = self.start_get()
        new_result = await self.next_search()
        new_result.set_result(self.fragments("fresh memory"))
        fresh = await new
        old_result.set_result(self.fragments("obsolete memory"))
        self.assertIsNone(await old)
        self.assertEqual(await self.provider.get(self.message), fresh)
        self.assertTrue(self.store.calls.empty())

    async def test_invalidation_wakes_existing_waiter_for_fresh_search(self):
        old = self.start_get()
        old_result = await self.next_search()
        waiter = self.start_get()
        await asyncio.sleep(0)
        await self.provider.invalidate("42")
        fresh_result = await self.next_search()
        fresh_result.set_result(self.fragments("fresh memory"))
        self.assertIn("fresh memory", await waiter)
        old_result.set_result(self.fragments("obsolete memory"))
        self.assertIsNone(await old)

    async def test_cancelled_obsolete_search_keeps_replacement_pending(self):
        old = self.start_get()
        await self.next_search()
        await self.provider.invalidate("42")
        new = self.start_get()
        result = await self.next_search()
        replacement_event = self.provider._pending_queries[self.key]
        old.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await old
        self.assertIs(self.provider._pending_queries[self.key], replacement_event)
        result.set_result(self.fragments("fresh memory"))
        self.assertIn("fresh memory", await new)

    async def test_failed_obsolete_search_keeps_replacement_pending(self):
        old = self.start_get()
        old_result = await self.next_search()
        await self.provider.invalidate("42")
        new = self.start_get()
        result = await self.next_search()
        replacement_event = self.provider._pending_queries[self.key]
        old_result.set_exception(RuntimeError("offline test failure"))
        self.assertIsNone(await old)
        self.report_error.assert_awaited_once()
        self.assertIs(self.provider._pending_queries[self.key], replacement_event)
        result.set_result(self.fragments("fresh memory"))
        self.assertIn("fresh memory", await new)

    async def test_cancellation_unblocks_waiter_to_retry(self):
        leader = self.start_get()
        await self.next_search()
        waiter = self.start_get()
        await asyncio.sleep(0)
        leader.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await leader
        result = await self.next_search()
        result.set_result(self.fragments("fresh memory"))
        self.assertIn("fresh memory", await waiter)
        self.assertNotIn(self.key, self.provider._pending_queries)

    async def test_search_error_unblocks_waiter_to_retry(self):
        leader = self.start_get()
        failed_result = await self.next_search()
        waiter = self.start_get()
        await asyncio.sleep(0)
        failed_result.set_exception(RuntimeError("offline test failure"))
        self.assertIsNone(await leader)
        self.report_error.assert_awaited_once()
        result = await self.next_search()
        result.set_result(self.fragments("fresh memory"))
        self.assertIn("fresh memory", await waiter)
        self.assertNotIn(self.key, self.provider._pending_queries)

    async def test_invalidation_evicts_completed_cached_result(self):
        old = self.start_get()
        old_result = await self.next_search()
        old_result.set_result(self.fragments("obsolete memory"))
        await old
        await self.provider.invalidate("42")
        self.assertNotIn(self.key, self.provider._cache)
        new = self.start_get()
        result = await self.next_search()
        result.set_result(self.fragments("fresh memory"))
        self.assertIn("fresh memory", await new)

    async def test_normal_concurrent_reads_share_result_and_cache(self):
        leader = self.start_get()
        result = await self.next_search()
        waiter = self.start_get()
        await asyncio.sleep(0)
        result.set_result(self.fragments("shared memory"))
        expected = await leader
        self.assertEqual(await waiter, expected)
        self.assertEqual(await self.provider.get(self.message), expected)
        self.assertTrue(self.store.calls.empty())

    async def test_other_channel_invalidation_preserves_active_search(self):
        leader = self.start_get()
        result = await self.next_search()
        await self.provider.invalidate("99")
        result.set_result(self.fragments("unaffected memory"))
        expected = await leader
        self.assertIn("unaffected memory", expected)
        self.assertEqual(await self.provider.get(self.message), expected)
        self.assertTrue(self.store.calls.empty())

    async def test_empty_results_are_cached(self):
        leader = self.start_get()
        result = await self.next_search()
        result.set_result([])
        self.assertIsNone(await leader)
        self.assertIsNone(await self.provider.get(self.message))
        self.assertTrue(self.store.calls.empty())


if __name__ == "__main__":
    unittest.main()
