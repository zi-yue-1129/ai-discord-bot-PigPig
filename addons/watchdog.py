"""Watchdog for a frozen event loop.

The bot once stayed offline for hours with its process alive: the event loop thread was stuck
waiting on a lock, so Discord's connection died, no message was logged and even SIGTERM was not
handled. A frozen loop cannot report itself, so a separate thread watches a heartbeat that the
loop updates. When the heartbeat stops, the watchdog writes where every thread is stuck (the
evidence needed to find the cause) and restarts the process.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import faulthandler
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, MutableMapping, Optional

from addons.logging import get_logger

log = get_logger(server_id="system", source=__name__)

# Environment variable carrying the number of consecutive watchdog restarts across restarts.
RESTARTS_ENV = "WATCHDOG_RESTARTS"
# Restarts in a row before the watchdog only records stalls (a restart loop helps nobody).
DEFAULT_MAX_RESTARTS = 3
# A process that ticked this long without a stall counts as healthy again.
HEALTHY_RESET_SECONDS = 600.0


def restart_process() -> None:
    """Replaces the running process by a fresh ``python <same arguments>`` (same PID, same terminal).

    Only returns by raising when the executable cannot be started.
    """
    os.execv(sys.executable, [sys.executable, *sys.argv])


class LoopWatchdog:
    """Detects an event loop that stopped ticking, records thread stacks and restarts the bot.

    Args:
        dump_dir: Where the stack dumps are written (one file per stall).
        stall_seconds: How long the loop may go without a tick before it counts as frozen.
        check_interval: How often the watchdog thread looks at the heartbeat.
        heartbeat_interval: How often the loop marks itself alive.
        restart: Called after a stall has been recorded (default: re-exec the process).
        max_restarts: Consecutive restarts allowed before only recording.
        clock: Monotonic clock (replaceable in tests).
        environ: Where the restart counter lives (replaceable in tests).
    """

    def __init__(
        self,
        dump_dir: Path,
        *,
        stall_seconds: float = 180.0,
        check_interval: float = 10.0,
        heartbeat_interval: float = 5.0,
        restart: Callable[[], None] = restart_process,
        max_restarts: int = DEFAULT_MAX_RESTARTS,
        clock: Callable[[], float] = time.monotonic,
        environ: Optional[MutableMapping[str, str]] = None,
    ) -> None:
        self._dump_dir = dump_dir
        self._stall_seconds = stall_seconds
        self._check_interval = check_interval
        self._heartbeat_interval = heartbeat_interval
        self._restart = restart
        self._max_restarts = max_restarts
        self._clock = clock
        self._environ = os.environ if environ is None else environ
        self._last_tick = clock()
        self._healthy_since = self._last_tick
        self._handled_tick: Optional[float] = None
        self._stopped = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._heartbeat_task: Optional[concurrent.futures.Future] = None

    @property
    def dump_dir(self) -> Path:
        """Returns the folder the stack dumps are written to."""
        return self._dump_dir

    def is_watching(self) -> bool:
        """Tells whether the watching thread is running."""
        return self._thread is not None and self._thread.is_alive()

    def tick(self) -> None:
        """Marks the event loop as alive right now."""
        self._last_tick = self._clock()

    async def heartbeat(self) -> None:
        """Runs on the event loop and ticks regularly until cancelled."""
        while True:
            self.tick()
            await asyncio.sleep(self._heartbeat_interval)

    def check(self) -> Optional[Path]:
        """Looks at the heartbeat once; on a new stall records the threads and restarts.

        Returns:
            The dump file when a stall was handled just now, otherwise ``None``.
        """
        now = self._clock()
        silent_for = now - self._last_tick
        restarts = self._restart_count()

        if silent_for < self._stall_seconds:
            if restarts and now - self._healthy_since >= HEALTHY_RESET_SECONDS:
                self._environ[RESTARTS_ENV] = "0"
            return None
        if self._handled_tick == self._last_tick:
            return None  # this stall was already handled
        self._handled_tick = self._last_tick
        self._healthy_since = now

        will_restart = restarts < self._max_restarts
        dump = self._write_dump(silent_for, restarts, will_restart)
        log.error(f"Event loop frozen for {silent_for:.0f}s; thread stacks written to {dump}.")
        if will_restart:
            self._environ[RESTARTS_ENV] = str(restarts + 1)
            self._restart()
        return dump

    def _restart_count(self) -> int:
        """Returns the consecutive watchdog restarts so far (0 when unknown)."""
        try:
            return int(self._environ.get(RESTARTS_ENV, "0"))
        except ValueError:
            return 0

    def _write_dump(self, silent_for: float, restarts: int, will_restart: bool) -> Path:
        """Writes a header and the stack of every thread to a new file."""
        self._dump_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self._dump_dir / f"stall-{stamp}.txt"
        action = "restarting" if will_restart else f"not restarting ({restarts} consecutive restarts already)"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(f"The event loop did not tick for {silent_for:.0f} seconds; {action}.\n\n")
            handle.flush()
            faulthandler.dump_traceback(file=handle, all_threads=True)
        return path

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """Starts the heartbeat on ``loop`` and the watching thread.

        Args:
            loop: The bot's event loop (it may already be running in another thread).
        """
        self.tick()
        self._heartbeat_task = asyncio.run_coroutine_threadsafe(self.heartbeat(), loop)
        self._thread = threading.Thread(target=self._watch, name="loop-watchdog", daemon=True)
        self._thread.start()

    def _watch(self) -> None:
        """Body of the watching thread."""
        while not self._stopped.wait(self._check_interval):
            try:
                self.check()
            except OSError:
                # The watchdog must never die silently: log the full error and keep watching.
                log.error("Loop watchdog check failed", exc_info=True)

    def stop(self) -> None:
        """Stops watching (and cancels the heartbeat)."""
        self._stopped.set()
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()


def start_loop_watchdog(loop: asyncio.AbstractEventLoop, root_dir: Path) -> LoopWatchdog:
    """Starts the bot's watchdog: stack dumps go to ``<root_dir>/logs/watchdog``.

    Args:
        loop: The bot's event loop.
        root_dir: The bot's root folder.

    Returns:
        The running watchdog.
    """
    dog = LoopWatchdog(root_dir / "logs" / "watchdog")
    dog.start(loop)
    log.info(f"Loop watchdog started: a stall of {dog._stall_seconds:.0f}s writes thread stacks and restarts the bot.")
    return dog
