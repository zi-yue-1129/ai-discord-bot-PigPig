"""Tests for background pre-downloading of upcoming queue entries."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Optional

import pytest
from music_cog.helpers import GUILD_ID, FakeChannel, make_song

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.prefetch import PREFETCH_LOOKAHEAD, Prefetcher
from cogs.music_lib.queue_manager import QueueManager


class FakeDownloader:
    """YouTube manager whose downloads can be gated and made to fail."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self.calls: List[str] = []
        self.gate: Optional[asyncio.Event] = None
        self.fail_urls: set[str] = set()

    async def download_audio(self, url: str, folder: str, ctx: Any) -> tuple:
        self.calls.append(url)
        if self.gate is not None:
            await self.gate.wait()
        if url in self.fail_urls:
            return None, "HTTP 403"
        path = self.folder / f"{url.rsplit('/', 1)[-1]}.mp3"
        path.write_bytes(b"audio")
        return {"file_path": str(path), "duration": 120}, None


def _song(index: int, **extra: Any) -> dict:
    song = make_song(index)
    song.pop("file_path")
    song.update(extra)
    return song


@pytest.fixture
def downloader(tmp_path: Path) -> FakeDownloader:
    return FakeDownloader(tmp_path)


@pytest.fixture
def queue_manager() -> QueueManager:
    return QueueManager(bot=SimpleNamespace(user=SimpleNamespace(id=1)))


@pytest.fixture
def prefetcher(downloader: FakeDownloader, queue_manager: QueueManager, tmp_path: Path) -> Prefetcher:
    return Prefetcher(
        get_youtube=lambda: downloader,
        queue_manager=queue_manager,
        get_folder=lambda guild_id: str(tmp_path),
    )


@pytest.fixture
def prefetch_ctx() -> PlaybackContext:
    return PlaybackContext(guild=SimpleNamespace(id=GUILD_ID), channel=FakeChannel(), user=SimpleNamespace(id=42))


async def _settle(prefetcher: Prefetcher) -> None:
    await prefetcher.wait_idle(GUILD_ID)


async def _until_download_starts(downloader: FakeDownloader) -> None:
    """Yields to the event loop until the first download has begun."""
    for _ in range(50):
        if downloader.calls:
            return
        await asyncio.sleep(0)
    raise AssertionError("the download never started")


@pytest.mark.asyncio
async def test_downloads_only_the_next_songs_within_the_lookahead(
    prefetcher: Prefetcher, queue_manager: QueueManager, downloader: FakeDownloader,
    prefetch_ctx: PlaybackContext,
) -> None:
    for index in range(PREFETCH_LOOKAHEAD + 2):
        await queue_manager.add_to_queue(GUILD_ID, _song(index))

    prefetcher.schedule(prefetch_ctx)
    await _settle(prefetcher)

    snapshot = queue_manager.get_queue_snapshot(GUILD_ID)
    assert len(downloader.calls) == PREFETCH_LOOKAHEAD
    assert all(song.get("file_path") for song in snapshot[:PREFETCH_LOOKAHEAD])
    assert not any(song.get("file_path") for song in snapshot[PREFETCH_LOOKAHEAD:])


@pytest.mark.asyncio
async def test_skips_live_streams_and_already_downloaded_songs(
    prefetcher: Prefetcher, queue_manager: QueueManager, downloader: FakeDownloader,
    prefetch_ctx: PlaybackContext,
) -> None:
    await queue_manager.add_to_queue(GUILD_ID, _song(0, is_live=True))
    await queue_manager.add_to_queue(GUILD_ID, _song(1, file_path="/already/there.mp3"))
    await queue_manager.add_to_queue(GUILD_ID, _song(2))

    prefetcher.schedule(prefetch_ctx)
    await _settle(prefetcher)

    assert downloader.calls == [_song(2)["url"]]


@pytest.mark.asyncio
async def test_a_failed_prefetch_is_not_retried_in_a_loop_and_never_raises(
    prefetcher: Prefetcher, queue_manager: QueueManager, downloader: FakeDownloader,
    prefetch_ctx: PlaybackContext,
) -> None:
    await queue_manager.add_to_queue(GUILD_ID, _song(0))
    downloader.fail_urls.add(_song(0)["url"])

    prefetcher.schedule(prefetch_ctx)
    await _settle(prefetcher)

    assert downloader.calls == [_song(0)["url"]]
    assert not queue_manager.get_queue_snapshot(GUILD_ID)[0].get("file_path")


@pytest.mark.asyncio
async def test_playback_waits_for_an_in_flight_prefetch_instead_of_downloading_twice(
    prefetcher: Prefetcher, queue_manager: QueueManager, downloader: FakeDownloader,
    prefetch_ctx: PlaybackContext,
) -> None:
    song = _song(0)
    await queue_manager.add_to_queue(GUILD_ID, song)
    downloader.gate = asyncio.Event()

    prefetcher.schedule(prefetch_ctx)
    await asyncio.sleep(0)  # let the worker start the download
    waiter = asyncio.create_task(prefetcher.ensure_downloaded(prefetch_ctx, song))
    await asyncio.sleep(0)
    downloader.gate.set()
    info, error = await waiter

    assert error is None
    assert Path(info["file_path"]).exists()
    assert len(downloader.calls) == 1


@pytest.mark.asyncio
async def test_ensure_downloaded_downloads_when_nothing_is_in_flight(
    prefetcher: Prefetcher, downloader: FakeDownloader, prefetch_ctx: PlaybackContext,
) -> None:
    info, error = await prefetcher.ensure_downloaded(prefetch_ctx, _song(5))

    assert error is None
    assert Path(info["file_path"]).exists()
    assert len(downloader.calls) == 1


@pytest.mark.asyncio
async def test_ensure_downloaded_retries_a_song_whose_prefetch_failed(
    prefetcher: Prefetcher, queue_manager: QueueManager, downloader: FakeDownloader,
    prefetch_ctx: PlaybackContext,
) -> None:
    song = _song(0)
    await queue_manager.add_to_queue(GUILD_ID, song)
    downloader.fail_urls.add(song["url"])
    prefetcher.schedule(prefetch_ctx)
    await _settle(prefetcher)
    downloader.fail_urls.clear()

    info, error = await prefetcher.ensure_downloaded(prefetch_ctx, song)

    assert error is None
    assert Path(info["file_path"]).exists()
    assert len(downloader.calls) == 2


@pytest.mark.asyncio
async def test_cancel_stops_the_worker(
    prefetcher: Prefetcher, queue_manager: QueueManager, downloader: FakeDownloader,
    prefetch_ctx: PlaybackContext,
) -> None:
    await queue_manager.add_to_queue(GUILD_ID, _song(0))
    await queue_manager.add_to_queue(GUILD_ID, _song(1))
    downloader.gate = asyncio.Event()
    prefetcher.schedule(prefetch_ctx)
    await _until_download_starts(downloader)

    await prefetcher.cancel(GUILD_ID)

    assert not prefetcher.is_running(GUILD_ID)
    assert len(downloader.calls) == 1


@pytest.mark.asyncio
async def test_scheduling_twice_runs_a_single_worker(
    prefetcher: Prefetcher, queue_manager: QueueManager, downloader: FakeDownloader,
    prefetch_ctx: PlaybackContext,
) -> None:
    await queue_manager.add_to_queue(GUILD_ID, _song(0))
    downloader.gate = asyncio.Event()

    prefetcher.schedule(prefetch_ctx)
    prefetcher.schedule(prefetch_ctx)
    await asyncio.sleep(0)
    downloader.gate.set()
    await _settle(prefetcher)

    assert len(downloader.calls) == 1


# --- integration with the cog -------------------------------------------------


@pytest.mark.asyncio
async def test_the_cog_uses_a_prefetched_file_instead_of_downloading_again(
    cog: YTMusic, ctx: PlaybackContext, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    downloader = FakeDownloader(tmp_path)
    monkeypatch.setattr(cog, "youtube", downloader)
    monkeypatch.setattr(cog.queue_manager, "get_guild_queue_and_folder", lambda guild_id: (cog.queue_manager.guild_queues.setdefault(guild_id, asyncio.Queue()), str(tmp_path)))
    await cog.queue_manager.add_to_queue(GUILD_ID, _song(0))
    cog.prefetcher.schedule(ctx)
    await cog.prefetcher.wait_idle(GUILD_ID)

    song = await cog._get_next_song(ctx, GUILD_ID, force_new=False)

    assert Path(song["file_path"]).exists()
    assert len(downloader.calls) == 1


@pytest.mark.asyncio
async def test_cleaning_up_the_session_cancels_prefetch_and_deletes_downloaded_files(
    cog: YTMusic, ctx: PlaybackContext, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    downloader = FakeDownloader(tmp_path)
    monkeypatch.setattr(cog, "youtube", downloader)
    monkeypatch.setattr(cog.queue_manager, "get_guild_queue_and_folder", lambda guild_id: (cog.queue_manager.guild_queues.setdefault(guild_id, asyncio.Queue()), str(tmp_path)))
    await cog.queue_manager.add_to_queue(GUILD_ID, _song(0))
    cog.prefetcher.schedule(ctx)
    await cog.prefetcher.wait_idle(GUILD_ID)
    assert os.listdir(tmp_path)

    await cog._cleanup_voice_session(GUILD_ID)

    assert os.listdir(tmp_path) == []
    assert not cog.prefetcher.is_running(GUILD_ID)
