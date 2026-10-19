"""Tests for resuming a streamed song where it dropped, from the downloaded file."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path
from typing import Any, List, Tuple

import pytest
from music_cog.helpers import GUILD_ID, FakeVoiceClient, make_song

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext

POLL_SECONDS = 30.0


class _Clock:
    """A monotonic clock that advances by ``step`` every time it is read."""

    def __init__(self, step: float) -> None:
        self.now = 0.0
        self.step = step

    def __call__(self) -> float:
        self.now += self.step
        return self.now


class _DroppingVoiceClient(FakeVoiceClient):
    """Plays for ``polls`` status checks, then stops by itself."""

    def __init__(self, channel: object, polls: int) -> None:
        super().__init__(channel)
        self.polls = polls
        self.sources: list = []

    def is_playing(self) -> bool:
        if self.polls > 0:
            self.polls -= 1
            return True
        return False

    def play(self, source: Any) -> None:
        self.sources.append(source)
        self.polls = 10**6
        self.playing = True


@pytest.fixture
def dropping(cog: YTMusic, guild: Any, monkeypatch: pytest.MonkeyPatch) -> _DroppingVoiceClient:
    client = _DroppingVoiceClient(object(), polls=3)
    guild.voice_client = client
    return client


@pytest.fixture
def recorder(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Replaces everything a resume touches with recorders."""
    record: dict = {"sources": [], "loops": [], "after_play": 0}

    def fake_source(song: dict, volume: float = 1.0, start_offset: float = 0.0) -> str:
        record["sources"].append(start_offset)
        return "source"

    async def fake_loop(ctx: Any, song: dict, start_offset: float = 0.0) -> None:
        record["loops"].append(start_offset)

    async def fake_after_play(ctx: Any, song: dict) -> None:
        record["after_play"] += 1

    real_sleep = asyncio.sleep

    async def no_sleep(*args: Any, **kwargs: Any) -> None:
        await real_sleep(0)

    monkeypatch.setattr(cog.audio_manager, "create_audio_source", fake_source)
    monkeypatch.setattr(cog, "_handle_after_play", fake_after_play)
    monkeypatch.setattr("cogs.music.asyncio.sleep", no_sleep)
    monkeypatch.setattr(cog, "_clock", _Clock(POLL_SECONDS))
    record["real_loop"] = type(cog)._player_loop
    monkeypatch.setattr(cog, "_player_loop", fake_loop)
    return record


def _streamed_song(tmp_path: Path, *, with_file: bool = True, duration: int = 600) -> dict:
    file = tmp_path / "abc.mp3"
    file.write_bytes(b"x")
    song = make_song(7) | {
        "file_path": str(file) if with_file else None,
        "stream_url": "https://u",
        "duration": duration,
        "streaming": True,
    }
    return song


async def _run_loop(cog: YTMusic, recorder: dict, ctx: PlaybackContext, song: dict) -> None:
    cog.state_manager.update_state(GUILD_ID, current_song=song)
    await recorder["real_loop"](cog, ctx, song)
    # Let a resumed player loop, which runs as its own task, start.
    await asyncio.sleep(0)
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_a_stream_that_ends_early_resumes_from_the_file_at_the_position_it_reached(
    cog: YTMusic, ctx: PlaybackContext, dropping: _DroppingVoiceClient, recorder: dict, tmp_path: Path
) -> None:
    song = _streamed_song(tmp_path)

    await _run_loop(cog, recorder, ctx, song)

    assert recorder["after_play"] == 0
    assert len(dropping.sources) == 1
    (offset,) = recorder["sources"]
    assert 60 <= offset <= 100
    assert recorder["loops"] == [offset]
    assert song["streaming"] is False
    assert song["resumes"] == 1


@pytest.mark.asyncio
async def test_a_song_that_reached_its_end_goes_on_to_the_next_one(
    cog: YTMusic, ctx: PlaybackContext, dropping: _DroppingVoiceClient, recorder: dict, tmp_path: Path
) -> None:
    song = _streamed_song(tmp_path, duration=100)

    await _run_loop(cog, recorder, ctx, song)

    assert recorder["after_play"] == 1
    assert recorder["sources"] == []


@pytest.mark.asyncio
async def test_a_skip_is_never_mistaken_for_a_dropped_stream(
    cog: YTMusic, ctx: PlaybackContext, dropping: _DroppingVoiceClient, recorder: dict, tmp_path: Path
) -> None:
    song = _streamed_song(tmp_path)
    cog.state_manager.update_state(GUILD_ID, user_stopped=True)

    await _run_loop(cog, recorder, ctx, song)

    assert recorder["sources"] == []
    assert recorder["after_play"] == 1
    assert cog.state_manager.get_state(GUILD_ID).user_stopped is False


@pytest.mark.asyncio
async def test_a_song_played_from_its_file_is_not_resumed(
    cog: YTMusic, ctx: PlaybackContext, dropping: _DroppingVoiceClient, recorder: dict, tmp_path: Path
) -> None:
    song = _streamed_song(tmp_path) | {"streaming": False}

    await _run_loop(cog, recorder, ctx, song)

    assert recorder["sources"] == []
    assert recorder["after_play"] == 1


@pytest.mark.asyncio
async def test_resuming_stops_after_the_configured_number_of_attempts(
    cog: YTMusic, ctx: PlaybackContext, dropping: _DroppingVoiceClient, recorder: dict, tmp_path: Path
) -> None:
    song = _streamed_song(tmp_path) | {"resumes": cog.service.streaming.max_resumes}

    await _run_loop(cog, recorder, ctx, song)

    assert recorder["sources"] == []
    assert recorder["after_play"] == 1


@pytest.mark.asyncio
async def test_resuming_can_be_switched_off(
    cog: YTMusic, ctx: PlaybackContext, dropping: _DroppingVoiceClient, recorder: dict, tmp_path: Path
) -> None:
    cog.service.streaming = replace(cog.service.streaming, enabled=False)
    song = _streamed_song(tmp_path)

    await _run_loop(cog, recorder, ctx, song)

    assert recorder["sources"] == []
    assert recorder["after_play"] == 1


@pytest.mark.asyncio
async def test_resume_waits_for_a_download_that_is_still_running(
    cog: YTMusic, ctx: PlaybackContext, dropping: _DroppingVoiceClient, recorder: dict,
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    song = _streamed_song(tmp_path, with_file=False)
    finished = tmp_path / "done.mp3"
    finished.write_bytes(b"x")
    release = asyncio.Event()

    class SlowYouTube:
        async def download_audio(self, url: str, folder: str, ctx: Any) -> Tuple[dict, None]:
            await release.wait()
            return {"file_path": str(finished)}, None

    monkeypatch.setattr(cog, "youtube", SlowYouTube())
    cog.prefetcher.download_current(ctx, song)
    loop_task = asyncio.create_task(_run_loop(cog, recorder, ctx, song))
    await asyncio.sleep(0.05)
    assert recorder["sources"] == []

    release.set()
    await asyncio.wait_for(loop_task, timeout=2)

    assert len(recorder["sources"]) == 1
    assert song["file_path"] == str(finished)


@pytest.mark.asyncio
async def test_resume_gives_up_to_the_next_song_when_the_download_failed(
    cog: YTMusic, ctx: PlaybackContext, dropping: _DroppingVoiceClient, recorder: dict,
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    song = _streamed_song(tmp_path, with_file=False)

    class FailingYouTube:
        async def download_audio(self, url: str, folder: str, ctx: Any) -> Tuple[None, str]:
            return None, "下載失敗"

    monkeypatch.setattr(cog, "youtube", FailingYouTube())

    await _run_loop(cog, recorder, ctx, song)

    assert recorder["sources"] == []
    assert recorder["after_play"] == 1


def test_a_skip_marks_the_state_so_the_player_loop_can_tell(
    cog: YTMusic, ctx: PlaybackContext
) -> None:
    states: List[bool] = []
    cog.state_manager.update_state(GUILD_ID, user_stopped=False)

    cog.mark_user_stop(GUILD_ID)
    states.append(cog.state_manager.get_state(GUILD_ID).user_stopped)

    assert states == [True]


@pytest.mark.asyncio
async def test_the_service_skip_marks_the_stop_as_the_users(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient
) -> None:
    voice_client.playing = True
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(0), user_stopped=False)

    await cog.service.skip(ctx)

    assert cog.state_manager.get_state(GUILD_ID).user_stopped is True
