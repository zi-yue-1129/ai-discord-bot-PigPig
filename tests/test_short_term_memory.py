"""Tests for the attachment LRU cache in ShortTermMemoryProvider."""

import asyncio
import datetime
from types import SimpleNamespace
from typing import Any, List

import pytest

import llm.utils.attachment_processor as attachment_processor
from addons.settings import attachment_config
from llm.memory.short_term import ShortTermMemoryProvider


class StubChannel:
    """Channel stub whose history yields a fixed list of messages."""

    def __init__(self, messages: List[Any]) -> None:
        """Store the messages returned (newest first) by ``history``.

        Args:
            messages: Messages ordered newest to oldest.
        """
        self._messages = messages

    async def history(self, limit: int):
        """Yield up to ``limit`` stored messages.

        Args:
            limit: Maximum number of messages to yield.

        Yields:
            Stub message objects.
        """
        for msg in self._messages[:limit]:
            yield msg


def _make_message(message_id: int, attachment_ids: List[int]) -> SimpleNamespace:
    """Build a minimal Discord message stub with attachments.

    Args:
        message_id: ID of the stub message.
        attachment_ids: IDs of the attachments on the message.

    Returns:
        A SimpleNamespace mimicking the discord.Message fields used by the provider.
    """
    attachments = [
        SimpleNamespace(id=att_id, filename=f"{att_id}.png", content_type="image/png", url="", size=1)
        for att_id in attachment_ids
    ]
    return SimpleNamespace(
        id=message_id,
        content="hello",
        attachments=attachments,
        embeds=[],
        reactions=[],
        reference=None,
        created_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        author=SimpleNamespace(name="user", id=42, bot=False),
    )


def _make_provider(max_cache_size: int = 100) -> ShortTermMemoryProvider:
    """Create a provider with a stub bot.

    Args:
        max_cache_size: Cache capacity passed to the provider.

    Returns:
        A ShortTermMemoryProvider instance.
    """
    bot = SimpleNamespace(user=SimpleNamespace(id=999))
    return ShortTermMemoryProvider(bot=bot, limit=10, max_cache_size=max_cache_size)


@pytest.fixture(autouse=True)
def _enable_attachments(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force attachment processing on regardless of local config."""
    monkeypatch.setattr(attachment_config, "enabled", True)


def test_successful_attachment_result_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    """A successfully processed attachment is not processed again on the next call."""
    calls: List[int] = []

    async def fake_process(att: Any) -> list:
        calls.append(att.id)
        return [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,AAAA"}}]

    monkeypatch.setattr(attachment_processor, "process_attachment", fake_process)
    provider = _make_provider()
    message = SimpleNamespace(channel=StubChannel([_make_message(1, [10])]))

    first = asyncio.run(provider.get(message))
    second = asyncio.run(provider.get(message))

    assert calls == [10]
    assert first[0].content[1]["type"] == "image_url"
    assert second[0].content[1]["type"] == "image_url"


def test_failed_attachment_result_is_not_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    """A transient processing failure must be retried on the next call, not cached."""
    calls: List[int] = []

    async def flaky_process(att: Any) -> list:
        calls.append(att.id)
        if len(calls) == 1:
            # Mirrors the fallback part process_attachment returns when processing raises.
            return [{"type": "text", "text": f"[Attachment processing failed: {att.filename}]"}]
        return [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,AAAA"}}]

    monkeypatch.setattr(attachment_processor, "process_attachment", flaky_process)
    provider = _make_provider()
    message = SimpleNamespace(channel=StubChannel([_make_message(1, [10])]))

    asyncio.run(provider.get(message))
    second = asyncio.run(provider.get(message))

    assert calls == [10, 10]
    assert second[0].content[1]["type"] == "image_url"


def test_cache_evicts_least_recently_used(monkeypatch: pytest.MonkeyPatch) -> None:
    """When capacity is exceeded, the least recently used attachment is evicted."""
    calls: List[int] = []

    async def fake_process(att: Any) -> list:
        calls.append(att.id)
        return [{"type": "text", "text": f"att-{att.id}"}]

    monkeypatch.setattr(attachment_processor, "process_attachment", fake_process)
    provider = _make_provider(max_cache_size=2)

    for att_id in (1, 2, 1, 3, 2):
        message = SimpleNamespace(channel=StubChannel([_make_message(att_id, [att_id])]))
        asyncio.run(provider.get(message))

    # 1 and 2 cached; 1 re-used (hit); 3 evicts 2 (LRU); 2 must be processed again.
    assert calls == [1, 2, 3, 2]


def test_negative_max_cache_size_raises() -> None:
    """A negative cache size is rejected at construction time."""
    with pytest.raises(ValueError, match="max_cache_size"):
        _make_provider(max_cache_size=-1)
