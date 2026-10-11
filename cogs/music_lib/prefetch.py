"""Background pre-downloading of upcoming queue entries.

Songs are downloaded and converted when their turn comes, which leaves a gap
of several seconds between tracks. While a song plays, :class:`Prefetcher`
downloads the next few queue entries in the background so they start instantly.

Downloads are shared: when playback reaches a song that is still being
prefetched it waits for that download instead of starting a second one.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional, Set, Tuple

from addons.logging import get_logger

from .context import PlaybackContext

log = get_logger(source=__name__, server_id="system")

# How many songs ahead of the current one are downloaded in the background.
PREFETCH_LOOKAHEAD = 2

DownloadResult = Tuple[Optional[Dict[str, Any]], Optional[str]]


class Prefetcher:
    """Downloads upcoming songs while another one plays.

    Args:
        get_youtube: Returns the YouTube manager (it is created after the cog).
        queue_manager: The queue manager holding each guild's queue.
        get_folder: Returns the download folder of a guild.
        lookahead: How many queue entries ahead to keep downloaded.
    """

    def __init__(
        self,
        get_youtube: Callable[[], Any],
        queue_manager: Any,
        get_folder: Callable[[int], str],
        lookahead: int = PREFETCH_LOOKAHEAD,
    ) -> None:
        self._get_youtube = get_youtube
        self._queue_manager = queue_manager
        self._get_folder = get_folder
        self._lookahead = lookahead
        self._workers: Dict[int, asyncio.Task] = {}
        self._inflight: Dict[Tuple[int, str], asyncio.Task] = {}
        self._failed: Dict[int, Set[str]] = {}

    # ------------------------------------------------------------------ public
    def schedule(self, ctx: PlaybackContext) -> None:
        """Starts the guild's background worker unless one is already running.

        Args:
            ctx: The playback context (used for the requester of downloads).
        """
        guild_id = ctx.guild.id
        worker = self._workers.get(guild_id)
        if worker is not None and not worker.done():
            return
        self._workers[guild_id] = asyncio.create_task(self._run(ctx, guild_id))

    def is_running(self, guild_id: int) -> bool:
        """Tells whether a background worker is active for the guild."""
        worker = self._workers.get(guild_id)
        return worker is not None and not worker.done()

    async def wait_idle(self, guild_id: int) -> None:
        """Waits until the guild's background worker has nothing left to do."""
        worker = self._workers.get(guild_id)
        if worker is not None:
            await worker

    async def ensure_downloaded(self, ctx: PlaybackContext, song: Dict[str, Any]) -> DownloadResult:
        """Makes sure ``song`` is downloaded, reusing an in-flight prefetch.

        Args:
            ctx: The playback context.
            song: The queue entry about to be played; updated in place.

        Returns:
            ``(download_info, None)`` on success, otherwise ``(None, error)``.
        """
        info, error = await self._download(ctx, ctx.guild.id, song)
        if not error:
            self._failed.get(ctx.guild.id, set()).discard(song["video_id"])
        return info, error

    async def cancel(self, guild_id: int) -> None:
        """Stops the guild's worker and any download it started."""
        tasks = [self._workers.pop(guild_id, None)]
        tasks.extend(task for (guild, _), task in list(self._inflight.items()) if guild == guild_id)
        pending = [task for task in tasks if task is not None and not task.done()]
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        self._failed.pop(guild_id, None)

    # ----------------------------------------------------------------- internals
    def _next_target(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Returns the first entry among the next downloadable songs that is missing its file.

        Live streams need no file, so they do not use up the lookahead window.
        """
        failed = self._failed.get(guild_id, set())
        window = [
            song
            for song in self._queue_manager.get_queue_snapshot(guild_id)
            if not song.get("is_live")
        ][: self._lookahead]
        for song in window:
            if song.get("file_path") or song.get("video_id") in failed:
                continue
            return song
        return None

    async def _run(self, ctx: PlaybackContext, guild_id: int) -> None:
        """Worker loop: download queue entries until none within the lookahead is missing."""
        while True:
            song = self._next_target(guild_id)
            if song is None:
                return
            try:
                _, error = await self._download(ctx, guild_id, song)
            except asyncio.CancelledError:
                raise
            except Exception:
                # Prefetching is best effort: the song is downloaded again when its
                # turn comes, so one failed attempt must not stop the worker.
                log.error("Prefetch failed for %s", song.get("title"), exc_info=True)
                error = "unexpected error"
            if error:
                log.warning("Prefetch of '%s' failed (%s); it will be retried when it plays.", song.get("title"), error)
                self._failed.setdefault(guild_id, set()).add(song["video_id"])

    async def _download(self, ctx: PlaybackContext, guild_id: int, song: Dict[str, Any]) -> DownloadResult:
        """Downloads ``song`` once, sharing the work between prefetch and playback."""
        key = (guild_id, song["video_id"])
        task = self._inflight.get(key)
        if task is None:
            task = asyncio.create_task(self._fetch(ctx, guild_id, song))
            self._inflight[key] = task
            task.add_done_callback(lambda finished, key=key: self._forget(key, finished))
        # shield: a cancelled waiter must not abort a download someone else needs.
        info, error = await asyncio.shield(task)
        if not error and info:
            song.update(info)
        return info, error

    def _forget(self, key: Tuple[int, str], finished: asyncio.Task) -> None:
        """Drops a finished download from the in-flight table."""
        if self._inflight.get(key) is finished:
            del self._inflight[key]

    async def _fetch(self, ctx: PlaybackContext, guild_id: int, song: Dict[str, Any]) -> DownloadResult:
        """Performs the actual download."""
        folder = self._get_folder(guild_id)
        return await self._get_youtube().download_audio(song["url"], folder, ctx)
