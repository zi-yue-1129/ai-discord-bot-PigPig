"""The watchdog notices a frozen event loop, records where every thread is stuck, and restarts the bot."""

from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path
from typing import Dict, List

import pytest

from addons.watchdog import RESTARTS_ENV, LoopWatchdog


class _Clock:
    """A clock the tests move by hand."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _watchdog(tmp_path: Path, clock: _Clock, environ: Dict[str, str], restarts: List[int], **kwargs: float) -> LoopWatchdog:
    return LoopWatchdog(
        tmp_path,
        stall_seconds=kwargs.get("stall_seconds", 180.0),
        restart=lambda: restarts.append(1),
        clock=clock,
        environ=environ,
    )


def test_a_loop_that_keeps_ticking_is_left_alone(tmp_path: Path) -> None:
    clock, restarts = _Clock(), []
    dog = _watchdog(tmp_path, clock, {}, restarts)
    dog.tick()
    clock.now += 179

    assert dog.check() is None
    assert restarts == []
    assert list(tmp_path.iterdir()) == []


def test_a_stalled_loop_is_dumped_and_the_bot_restarted(tmp_path: Path) -> None:
    clock, restarts, environ = _Clock(), [], {}
    dog = _watchdog(tmp_path, clock, environ, restarts)
    dog.tick()
    clock.now += 181

    dump = dog.check()

    assert dump is not None and dump.parent == tmp_path
    text = dump.read_text(encoding="utf-8")
    assert "event loop did not tick for 181" in text
    assert "MainThread" in text or "Thread 0x" in text or "Current thread" in text
    assert restarts == [1]
    assert environ[RESTARTS_ENV] == "1"


def test_one_stall_is_handled_only_once(tmp_path: Path) -> None:
    clock, restarts = _Clock(), []
    dog = _watchdog(tmp_path, clock, {}, restarts)
    dog.tick()
    clock.now += 200
    dog.check()

    clock.now += 50

    assert dog.check() is None
    assert restarts == [1]


def test_after_too_many_consecutive_restarts_it_only_records(tmp_path: Path) -> None:
    clock, restarts, environ = _Clock(), [], {RESTARTS_ENV: "3"}
    dog = _watchdog(tmp_path, clock, environ, restarts)
    dog.tick()
    clock.now += 200

    dump = dog.check()

    assert dump == next(tmp_path.iterdir())
    assert "not restarting" in dump.read_text(encoding="utf-8")
    assert restarts == []


def test_a_healthy_stretch_resets_the_restart_count(tmp_path: Path) -> None:
    clock, restarts, environ = _Clock(), [], {RESTARTS_ENV: "2"}
    dog = _watchdog(tmp_path, clock, environ, restarts)
    for _ in range(20):
        clock.now += 60
        dog.tick()
        dog.check()

    assert environ[RESTARTS_ENV] == "0"


@pytest.mark.asyncio
async def test_the_heartbeat_marks_the_loop_as_alive(tmp_path: Path) -> None:
    clock, restarts = _Clock(), []
    dog = LoopWatchdog(tmp_path, restart=lambda: restarts.append(1), clock=clock, environ={}, heartbeat_interval=0.01)
    dog.tick()
    clock.now += 500

    task = asyncio.create_task(dog.heartbeat())
    await asyncio.sleep(0.05)
    task.cancel()

    assert dog.check() is None


def test_a_really_blocked_loop_is_caught_by_the_watchdog_thread(tmp_path: Path) -> None:
    restarted = threading.Event()
    dog = LoopWatchdog(
        tmp_path,
        stall_seconds=0.3,
        check_interval=0.05,
        heartbeat_interval=0.05,
        restart=restarted.set,
        environ={},
    )
    loop = asyncio.new_event_loop()
    worker = threading.Thread(target=loop.run_forever, daemon=True)
    worker.start()
    try:
        dog.start(loop)
        time.sleep(0.2)
        assert not restarted.is_set()

        loop.call_soon_threadsafe(time.sleep, 1.0)

        assert restarted.wait(timeout=3.0)
        assert len(list(tmp_path.iterdir())) == 1
    finally:
        dog.stop()
        loop.call_soon_threadsafe(loop.stop)
        worker.join(timeout=3.0)
        loop.close()


def test_the_bots_watchdog_starts_with_dumps_under_logs_watchdog(tmp_path: Path) -> None:
    from addons.watchdog import start_loop_watchdog

    loop = asyncio.new_event_loop()
    worker = threading.Thread(target=loop.run_forever, daemon=True)
    worker.start()
    try:
        dog = start_loop_watchdog(loop, tmp_path)

        assert dog.dump_dir == tmp_path / "logs" / "watchdog"
        assert dog.is_watching()
    finally:
        dog.stop()
        loop.call_soon_threadsafe(loop.stop)
        worker.join(timeout=3.0)
        loop.close()
