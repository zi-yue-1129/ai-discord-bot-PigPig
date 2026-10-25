"""Regression tests for bugs found by auditing the music feature."""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Tuple

import pytest
from music_cog.helpers import (
    GUILD_ID,
    FakeChannel,
    FakeVoiceClient,
    make_interaction,
    make_member,
    make_song,
)
from music_cog.test_service import FakeYouTube

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.queue_manager import PlayMode
from cogs.music_lib.youtube import YouTubeManager


@pytest.fixture
def youtube(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> FakeYouTube:
    fake = FakeYouTube()
    monkeypatch.setattr(cog, "youtube", fake)
    return fake


@pytest.fixture
def wired_player(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> List[Any]:
    """Replaces audio, UI and the player loop with fakes; returns the started loops."""
    loops: List[dict] = []

    def fake_source(song: dict, volume: float = 1.0, start_offset: float = 0.0) -> str:
        return "source"

    async def fake_ui(*args: Any, **kwargs: Any) -> None:
        return None

    def fake_loop(ctx: Any, song: dict, start_offset: float = 0.0) -> Any:
        # Recorded when the loop is created: the task itself runs on the bot's own event loop.
        loops.append(song)
        return asyncio.sleep(0)

    monkeypatch.setattr(cog.audio_manager, "create_audio_source", fake_source)
    monkeypatch.setattr(cog.ui_manager, "update_player_ui", fake_ui, raising=False)
    monkeypatch.setattr(cog, "_player_loop", fake_loop)
    return loops


# ------------------------------------------------------------- single loop (NameError)


@pytest.mark.asyncio
async def test_single_loop_replays_the_song_while_audio_is_still_playing(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, wired_player: List[Any]
) -> None:
    song = make_song(1)
    cog.state_manager.update_state(GUILD_ID, current_song=song)
    voice_client.playing = True

    await cog._handle_single_loop(ctx, cog.state_manager.get_state(GUILD_ID), voice_client)

    assert voice_client.stop_calls == 1
    assert voice_client.sources == ["source"]
    assert cog.state_manager.get_state(GUILD_ID).consecutive_failures == 0


@pytest.mark.asyncio
async def test_each_single_loop_repeat_is_counted_as_a_play(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, wired_player: List[Any]
) -> None:
    song = make_song(1)
    cog.state_manager.update_state(GUILD_ID, current_song=song)

    await cog._handle_single_loop(ctx, cog.state_manager.get_state(GUILD_ID), voice_client)
    first = song["play_event_id"]
    cog.state_manager.update_state(GUILD_ID, current_song=song)
    await cog._handle_single_loop(ctx, cog.state_manager.get_state(GUILD_ID), voice_client)

    assert song["play_event_id"] != first
    assert [plays for _, _, plays, _ in cog._taste_store.top_played(GUILD_ID, 0, 1e12)] == [2]


# ------------------------------------------------------- idle timer against play()


@pytest.mark.asyncio
async def test_playing_cancels_a_pending_idle_disconnect_before_the_slow_lookup(
    cog: YTMusic, ctx: PlaybackContext, youtube: FakeYouTube, monkeypatch: pytest.MonkeyPatch
) -> None:
    timer = asyncio.create_task(asyncio.sleep(100))
    cog.disconnect_timers[GUILD_ID] = timer
    seen: List[bool] = []

    async def lookup(url: str, context: Any) -> Tuple[None, None]:
        seen.append(GUILD_ID in cog.disconnect_timers)
        return None, None

    async def fake_play_next(source: Any, force_new: bool = False) -> None:
        PlaybackContext.coerce(source).guild.voice_client.playing = True

    monkeypatch.setattr(youtube, "resolve_stream", lookup)
    monkeypatch.setattr(cog, "play_next", fake_play_next)

    await cog.service.play(ctx, "怪物")
    await asyncio.sleep(0)

    assert seen == [False]
    assert timer.cancelled()


@pytest.mark.asyncio
async def test_a_bot_that_left_during_the_lookup_reports_it_and_keeps_no_stale_song(
    cog: YTMusic, ctx: PlaybackContext, guild: SimpleNamespace, youtube: FakeYouTube,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def lookup(url: str, context: Any) -> Tuple[dict, None]:
        guild.voice_client = None
        return make_song(5) | {"file_path": None, "stream_url": "https://u"}, None

    monkeypatch.setattr(youtube, "resolve_stream", lookup)

    result = await cog.service.play(ctx, "怪物")

    assert not result.ok
    assert result.reason == "voice_connect_failed"
    assert cog.queue_manager.get_queue_snapshot(GUILD_ID) == []


# ------------------------------------------------------------- orphan downloads


class _SlowYouTube:
    """A download that finishes only when the test says so, leaving a real file."""

    def __init__(self, file: Path) -> None:
        self.file = file
        self.release = asyncio.Event()

    async def download_audio(self, url: str, folder: str, ctx: Any) -> Tuple[dict, None]:
        await self.release.wait()
        self.file.write_bytes(b"audio")
        return {"file_path": str(self.file)}, None


class _BlockingYoutubeDL:
    """A yt-dlp stand-in whose download runs in a thread that cannot be cancelled."""

    started = threading.Event()
    release = threading.Event()
    written = threading.Event()

    def __init__(self, opts: dict) -> None:
        self.opts = opts

    def __enter__(self) -> "_BlockingYoutubeDL":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None

    def extract_info(self, url: str, download: bool = False) -> dict:
        return {"id": "abc", "title": "t", "duration": 100, "uploader": "u", "webpage_url": url}

    def download(self, urls: list) -> None:
        type(self).started.set()
        type(self).release.wait(timeout=5)
        Path(self.opts["outtmpl"].replace("%(id)s", "abc") + ".mp3").write_bytes(b"audio")
        type(self).written.set()


@pytest.mark.asyncio
async def test_a_download_that_finishes_after_it_was_cancelled_does_not_leave_its_file_behind(
    ctx: PlaybackContext, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for event in (_BlockingYoutubeDL.started, _BlockingYoutubeDL.release, _BlockingYoutubeDL.written):
        event.clear()
    monkeypatch.setattr("cogs.music_lib.youtube.yt_dlp.YoutubeDL", _BlockingYoutubeDL)
    manager = YouTubeManager()
    task = asyncio.create_task(manager.download_audio("https://youtu.be/abc", str(tmp_path), ctx))
    assert await asyncio.to_thread(_BlockingYoutubeDL.started.wait, 5)

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    _BlockingYoutubeDL.release.set()
    assert await asyncio.to_thread(_BlockingYoutubeDL.written.wait, 5)
    for _ in range(40):
        if not (tmp_path / "abc.mp3").exists():
            break
        await asyncio.sleep(0.05)

    assert not (tmp_path / "abc.mp3").exists()


@pytest.mark.asyncio
async def test_clearing_the_queue_keeps_the_background_download_of_the_playing_song(
    cog: YTMusic, ctx: PlaybackContext, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    slow = _SlowYouTube(tmp_path / "playing.mp3")
    monkeypatch.setattr(cog, "youtube", slow)
    song = make_song(4) | {"file_path": None, "stream_url": "https://u"}
    task = cog.prefetcher.download_current(ctx, song)
    await asyncio.sleep(0)

    await cog.service.clear_queue(ctx)
    slow.release.set()
    await asyncio.wait_for(task, timeout=2)

    assert not task.cancelled()
    assert song["file_path"] == str(slow.file)
    assert slow.file.exists()


# ------------------------------------------------------------------ paused player


def test_a_paused_player_does_not_count_as_idle(cog: YTMusic, voice_client: FakeVoiceClient) -> None:
    voice_client.paused = True

    assert cog._is_idle(voice_client) is False


def test_a_stopped_player_counts_as_idle(cog: YTMusic, voice_client: FakeVoiceClient) -> None:
    assert cog._is_idle(voice_client) is True


# ----------------------------------------------------------- playlist buffer


@pytest.mark.asyncio
async def test_leaving_the_voice_channel_drops_the_buffered_playlist(
    cog: YTMusic, monkeypatch: pytest.MonkeyPatch
) -> None:
    cog.queue_manager.set_playlist(GUILD_ID, [make_song(i) for i in range(20)])

    await cog._cleanup_voice_session(GUILD_ID)

    assert cog.queue_manager.has_playlist_songs(GUILD_ID) is False


# ------------------------------------------------- resume: progress bar and counter


class _ProgressView:
    """Records how the progress updater was restarted."""

    def __init__(self) -> None:
        self.restarts: List[Tuple[int, int]] = []
        self.current_position = 0

    def start_progress_updater(self, duration: int, start_position: int = 0) -> None:
        self.restarts.append((duration, start_position))


@pytest.mark.asyncio
async def test_the_progress_bar_is_restarted_at_the_resumed_position(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, tmp_path: Path,
    wired_player: List[Any],
) -> None:
    file = tmp_path / "abc.mp3"
    file.write_bytes(b"x")
    song = make_song(7) | {"file_path": str(file), "stream_url": "https://u", "duration": 600, "streaming": True}
    cog.state_manager.update_state(GUILD_ID, current_song=song)
    view = _ProgressView()
    cog.ui_manager.get_current_view = lambda guild_id: view

    resumed = await cog._resume_dropped_stream(ctx, song, 90.0)

    assert resumed is True
    assert view.restarts == [(600, 90)]


@pytest.mark.asyncio
async def test_a_fresh_play_gives_the_song_a_full_resume_budget(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, wired_player: List[Any]
) -> None:
    song = make_song(1) | {"resumes": 2}

    await cog._play_song(ctx, song, voice_client)

    assert song["resumes"] == 0


# ------------------------------------------------------- skip in single loop mode


@pytest.mark.asyncio
async def test_skip_marks_that_the_next_song_must_really_be_a_new_one(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient
) -> None:
    voice_client.playing = True
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(0))

    await cog.service.skip(ctx)

    assert cog.state_manager.get_state(GUILD_ID).force_next is True


@pytest.mark.asyncio
async def test_after_a_skip_play_next_is_forced_to_leave_the_looped_song(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: List[bool] = []

    async def record(source: Any, force_new: bool = False) -> None:
        calls.append(force_new)

    monkeypatch.setattr(cog, "play_next", record)
    cog.queue_manager.set_play_mode(GUILD_ID, PlayMode.LOOP_SINGLE)
    song = make_song(1)
    cog.state_manager.update_state(GUILD_ID, current_song=song, force_next=True)

    await cog._handle_after_play(ctx, song)

    assert calls == [True]
    assert cog.state_manager.get_state(GUILD_ID).force_next is False


@pytest.mark.asyncio
async def test_without_a_skip_the_looped_song_repeats(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: List[bool] = []

    async def record(source: Any, force_new: bool = False) -> None:
        calls.append(force_new)

    monkeypatch.setattr(cog, "play_next", record)
    cog.queue_manager.set_play_mode(GUILD_ID, PlayMode.LOOP_SINGLE)
    song = make_song(1)
    cog.state_manager.update_state(GUILD_ID, current_song=song)

    await cog._handle_after_play(ctx, song)

    assert calls == [False]


# ---------------------------------------------------------------- live streams


@pytest.mark.asyncio
async def test_a_live_stream_is_watched_so_the_queue_moves_on_when_it_ends(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, wired_player: List[Any]
) -> None:
    live = make_song(9) | {"is_live": True, "file_path": None, "stream_url": "https://live"}

    await cog._play_song(ctx, live, voice_client)
    await asyncio.sleep(0)

    assert wired_player == [live]


# ---------------------------------------------------------------- authorization


@pytest.mark.asyncio
async def test_mode_cannot_be_changed_from_outside_the_bots_channel(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, voice_client: FakeVoiceClient
) -> None:
    outsider = make_member(99, voice_channel=object())
    interaction = make_interaction(guild, text_channel, outsider)
    cog.queue_manager.set_play_mode(GUILD_ID, PlayMode.NO_LOOP)

    await cog.mode.callback(cog, interaction, SimpleNamespace(value="loop_single"))

    assert cog.queue_manager.get_play_mode(GUILD_ID) == PlayMode.NO_LOOP
    assert interaction.response.sent


@pytest.mark.asyncio
async def test_shuffle_cannot_be_toggled_from_outside_the_bots_channel(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, voice_client: FakeVoiceClient
) -> None:
    outsider = make_member(99, voice_channel=object())
    interaction = make_interaction(guild, text_channel, outsider)
    before = cog.queue_manager.is_shuffle_enabled(GUILD_ID)

    await cog.shuffle.callback(cog, interaction)

    assert cog.queue_manager.is_shuffle_enabled(GUILD_ID) == before
    assert interaction.response.sent
