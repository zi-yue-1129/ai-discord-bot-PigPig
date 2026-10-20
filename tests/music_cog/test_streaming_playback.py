"""Tests for playing the first song from its stream URL while it downloads in the background."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import Any, List, Optional

import pytest
from music_cog.helpers import GUILD_ID, FakeVoiceClient, make_song
from music_cog.test_service import FakeYouTube

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.service import MusicService

STREAM_URL = "https://rr1.googlevideo.com/audio"


def _stream_song(index: int = 7) -> dict:
    song = make_song(index) | {"file_path": None, "stream_url": STREAM_URL, "stream_headers": {"User-Agent": "UA"}}
    return song


@pytest.fixture
def youtube(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> FakeYouTube:
    fake = FakeYouTube()
    monkeypatch.setattr(cog, "youtube", fake)
    return fake


@pytest.fixture
def played(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> List[PlaybackContext]:
    calls: List[PlaybackContext] = []

    async def fake_play_next(source: Any, force_new: bool = False) -> None:
        context = PlaybackContext.coerce(source)
        calls.append(context)
        context.guild.voice_client.playing = True

    monkeypatch.setattr(cog, "play_next", fake_play_next)
    return calls


# ----------------------------------------------------------------------------- service


@pytest.mark.asyncio
async def test_the_first_song_is_queued_from_its_stream_without_downloading(
    cog: YTMusic, ctx: PlaybackContext, youtube: FakeYouTube, played: List[PlaybackContext]
) -> None:
    youtube.stream_song = _stream_song()

    result = await cog.service.play(ctx, "怪物")

    assert result.ok
    assert result.data["title"] == "song 7"
    assert youtube.downloaded == []
    assert len(played) == 1


@pytest.mark.asyncio
async def test_without_a_usable_stream_the_song_is_downloaded_as_before(
    cog: YTMusic, ctx: PlaybackContext, youtube: FakeYouTube, played: List[PlaybackContext]
) -> None:
    youtube.stream_song = None

    result = await cog.service.play(ctx, "怪物")

    assert result.ok
    assert youtube.downloaded == [youtube.search_results[0]["url"]]


@pytest.mark.asyncio
async def test_a_rejected_video_is_not_downloaded_after_the_stream_lookup_refused_it(
    cog: YTMusic, ctx: PlaybackContext, youtube: FakeYouTube, played: List[PlaybackContext]
) -> None:
    youtube.stream_error = "影片時長過長！超過 30 分鐘"
    youtube.search_results = [youtube.search_results[0]]

    result = await cog.service.play(ctx, "完整專輯")

    assert not result.ok
    assert result.reason == "lookup_failed"
    assert youtube.downloaded == []


@pytest.mark.asyncio
async def test_streaming_can_be_switched_off(
    cog: YTMusic, ctx: PlaybackContext, youtube: FakeYouTube, played: List[PlaybackContext]
) -> None:
    youtube.stream_song = _stream_song()
    cog.service.streaming = replace(cog.service.streaming, enabled=False)

    await cog.service.play(ctx, "怪物")

    assert youtube.resolved == []
    assert youtube.downloaded == [youtube.search_results[0]["url"]]


@pytest.mark.asyncio
async def test_a_song_queued_behind_a_playing_one_is_not_streamed(
    cog: YTMusic, ctx: PlaybackContext, youtube: FakeYouTube, played: List[PlaybackContext],
    voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True
    youtube.stream_song = _stream_song()

    await cog.service.play(ctx, "怪物")

    assert youtube.resolved == []


def test_the_cog_gives_the_service_the_configured_streaming_settings(cog: YTMusic) -> None:
    assert isinstance(cog.service, MusicService)
    assert cog.service.streaming == cog.settings.streaming


# ----------------------------------------------------------------------------- playback


class _Downloads:
    """A controllable ``download_audio`` so tests decide when a download finishes."""

    def __init__(self) -> None:
        self.release = asyncio.Event()
        self.urls: List[str] = []

    async def download_audio(self, url: str, folder: str, ctx: Any) -> tuple:
        self.urls.append(url)
        await self.release.wait()
        return {"file_path": "/tmp/stream-test.mp3", "title": "song 7"}, None


@pytest.fixture
def downloads(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> _Downloads:
    fake = _Downloads()
    monkeypatch.setattr(cog, "youtube", fake)
    return fake


@pytest.fixture
def wired_player(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> List[Any]:
    """Replaces audio and UI with fakes; returns the list of created audio sources."""
    sources: List[Any] = []

    def fake_source(song: dict, volume: float = 1.0, start_offset: float = 0.0, audio_filter: Optional[str] = None) -> str:
        sources.append((dict(song), start_offset))
        return "source"

    async def fake_ui(*args: Any, **kwargs: Any) -> None:
        return None

    async def idle_loop(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(cog.audio_manager, "create_audio_source", fake_source)
    monkeypatch.setattr(cog.ui_manager, "update_player_ui", fake_ui, raising=False)
    monkeypatch.setattr(cog, "_player_loop", idle_loop)
    return sources


@pytest.mark.asyncio
async def test_a_streamed_song_without_a_file_is_played_without_waiting_for_a_download(
    cog: YTMusic, ctx: PlaybackContext, downloads: _Downloads, wired_player: List[Any],
    voice_client: FakeVoiceClient,
) -> None:
    song = _stream_song()
    await cog.queue_manager.add_to_queue(GUILD_ID, song)

    await asyncio.wait_for(cog.play_next(ctx), timeout=2)

    assert voice_client.sources == ["source"]
    assert wired_player[0][0]["stream_url"] == STREAM_URL
    downloads.release.set()
    await cog.prefetcher.wait_current_download(GUILD_ID)


@pytest.mark.asyncio
async def test_a_streamed_song_is_downloaded_in_the_background_and_gets_its_file_path(
    cog: YTMusic, ctx: PlaybackContext, downloads: _Downloads, wired_player: List[Any],
) -> None:
    song = _stream_song()
    await cog.queue_manager.add_to_queue(GUILD_ID, song)

    await cog.play_next(ctx)
    assert song["file_path"] is None
    downloads.release.set()
    await cog.prefetcher.wait_current_download(GUILD_ID)

    assert downloads.urls == [song["url"]]
    assert song["file_path"] == "/tmp/stream-test.mp3"


@pytest.mark.asyncio
async def test_a_song_that_already_has_a_file_is_not_downloaded_again(
    cog: YTMusic, ctx: PlaybackContext, downloads: _Downloads, wired_player: List[Any],
) -> None:
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(1))

    await cog.play_next(ctx)
    await cog.prefetcher.wait_current_download(GUILD_ID)

    assert downloads.urls == []


@pytest.mark.asyncio
async def test_the_file_is_removed_even_when_the_song_ends_before_its_download_finished(
    cog: YTMusic, ctx: PlaybackContext, downloads: _Downloads, wired_player: List[Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deleted: List[Optional[str]] = []

    async def record_delete(guild_id: int, file_path: str) -> None:
        deleted.append(file_path)

    async def no_next(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(cog.audio_manager, "delete_file", record_delete)
    monkeypatch.setattr(cog, "play_next", no_next)
    song = _stream_song()
    await cog.queue_manager.add_to_queue(GUILD_ID, song)
    await cog.play_next(ctx)
    cog.state_manager.update_state(GUILD_ID, current_song=song)
    # play_next is stubbed above, so start the background download the way playback does.
    await cog._play_song(ctx, song, ctx.guild.voice_client)

    await cog._handle_after_play(ctx, song)
    assert deleted == []
    downloads.release.set()
    await asyncio.gather(*cog._cleanup_tasks)

    assert deleted == ["/tmp/stream-test.mp3"]


@pytest.mark.asyncio
async def test_stopping_cancels_the_background_download(
    cog: YTMusic, ctx: PlaybackContext, downloads: _Downloads, wired_player: List[Any],
) -> None:
    song = _stream_song()
    await cog.queue_manager.add_to_queue(GUILD_ID, song)
    await cog.play_next(ctx)
    await asyncio.sleep(0)

    await cog.prefetcher.cancel(GUILD_ID)

    assert cog.prefetcher.current_download(GUILD_ID) is None
