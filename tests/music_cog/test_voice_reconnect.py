"""Tests that the player loop survives Discord's short voice reconnects."""

from __future__ import annotations

import asyncio
from typing import Any, List

import pytest
from music_cog.helpers import GUILD_ID, FakeVoiceClient, make_song

from cogs.music import VOICE_RECONNECT_GRACE_SECONDS, YTMusic
from cogs.music_lib.context import PlaybackContext


class _ReconnectingVoiceClient(FakeVoiceClient):
    """Reports a dropped connection for ``dropped_checks`` status checks, then a live one.

    Once connected it plays for ``playing_checks`` checks and then the song ends.
    """

    def __init__(self, channel: object, dropped_checks: int, playing_checks: int) -> None:
        super().__init__(channel)
        self.dropped_checks = dropped_checks
        self.playing_checks = playing_checks

    def is_connected(self) -> bool:
        if self.dropped_checks > 0:
            self.dropped_checks -= 1
            return False
        return True

    def is_playing(self) -> bool:
        if self.playing_checks > 0:
            self.playing_checks -= 1
            return True
        return False


@pytest.fixture
def after_play_calls(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> List[str]:
    """Records the songs that reach the end-of-song handler, without sleeping for real."""
    calls: List[str] = []

    async def fake_after_play(ctx: Any, song: dict) -> None:
        calls.append(song["video_id"])

    real_sleep = asyncio.sleep

    async def no_sleep(*args: Any, **kwargs: Any) -> None:
        await real_sleep(0)

    monkeypatch.setattr(cog, "_handle_after_play", fake_after_play)
    monkeypatch.setattr("cogs.music.asyncio.sleep", no_sleep)
    return calls


async def _run_loop(cog: YTMusic, ctx: PlaybackContext, song: dict) -> None:
    cog.state_manager.update_state(GUILD_ID, current_song=song)
    await cog._player_loop(ctx, song)


@pytest.mark.asyncio
async def test_a_short_voice_reconnect_does_not_end_the_player_loop(
    cog: YTMusic, ctx: PlaybackContext, guild: Any, after_play_calls: List[str]
) -> None:
    # Discord drops the voice connection for a moment and discord.py reconnects by itself.
    guild.voice_client = _ReconnectingVoiceClient(object(), dropped_checks=3, playing_checks=2)
    song = make_song(1)

    await _run_loop(cog, ctx, song)

    assert after_play_calls == [song["video_id"]]


@pytest.mark.asyncio
async def test_a_connection_that_never_returns_ends_the_player_loop(
    cog: YTMusic, ctx: PlaybackContext, guild: Any, after_play_calls: List[str]
) -> None:
    guild.voice_client = _ReconnectingVoiceClient(
        object(), dropped_checks=VOICE_RECONNECT_GRACE_SECONDS + 5, playing_checks=2
    )

    await _run_loop(cog, ctx, make_song(1))

    assert after_play_calls == []
    assert guild.voice_client.dropped_checks > 0
