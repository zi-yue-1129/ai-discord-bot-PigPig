"""A message arriving while a channel summary runs must not cancel that summary."""
import asyncio
from types import SimpleNamespace

import discord
import pytest

from cogs.memory.services.message_tracker import MessageTracker


class _Channel(discord.TextChannel):
    def __init__(self, channel_id):
        self.id = channel_id


def _tracker(delay=0.01):
    settings = SimpleNamespace(processing_delay=delay, processing_concurrency=1)
    return MessageTracker(bot=None, storage=None, settings=settings)


@pytest.mark.asyncio
async def test_new_message_does_not_cancel_a_running_pass():
    tracker = _tracker()
    started, release, finished = asyncio.Event(), asyncio.Event(), []

    async def fake_process(channel):
        started.set()
        await release.wait()
        finished.append(channel.id)

    tracker._process_channel_memory = fake_process
    channel = _Channel(1)

    tracker._schedule_processing(channel)
    await asyncio.wait_for(started.wait(), 1)
    # Messages keep arriving in the busy channel while the LLM works.
    for _ in range(3):
        tracker._schedule_processing(channel)
    release.set()
    await asyncio.wait_for(tracker._processing_tasks[1], 1)

    assert finished == [1]
    assert 1 not in tracker._running_channels


@pytest.mark.asyncio
async def test_new_message_still_debounces_a_waiting_pass():
    tracker = _tracker(delay=0.05)
    calls = []

    async def fake_process(channel):
        calls.append(channel.id)

    tracker._process_channel_memory = fake_process
    channel = _Channel(2)

    tracker._schedule_processing(channel)
    first = tracker._processing_tasks[2]
    tracker._schedule_processing(channel)
    await asyncio.wait_for(tracker._processing_tasks[2], 1)
    await asyncio.sleep(0)

    assert first.cancelled() or first.done()
    assert calls == [2]


@pytest.mark.asyncio
async def test_interrupt_all_still_stops_a_running_pass():
    tracker = _tracker()
    started = asyncio.Event()
    state = {}

    async def fake_process(channel):
        tracker._active_summarization_task = asyncio.current_task()
        started.set()
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            state["interrupted"] = True

    tracker._process_channel_memory = fake_process
    channel = _Channel(3)
    tracker._schedule_processing(channel)
    task = tracker._processing_tasks[3]
    await asyncio.wait_for(started.wait(), 1)

    tracker.interrupt_all()
    await asyncio.wait_for(asyncio.gather(task, return_exceptions=True), 1)

    assert state == {"interrupted": True}
    assert 3 not in tracker._running_channels
