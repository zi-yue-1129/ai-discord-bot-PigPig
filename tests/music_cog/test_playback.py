"""Tests for playback failure handling and playback authorization."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from cogs.music import MAX_CONSECUTIVE_FAILURES, YTMusic
from cogs.music_lib.context import PlaybackContext
from music_cog.helpers import (
    GUILD_ID,
    FakeChannel,
    FakeControlView,
    FakeVoiceClient,
    make_interaction,
    make_member,
    make_song,
)

SAFETY_CAP = 25


async def _fill_queue(cog: YTMusic, count: int) -> None:
    for index in range(count):
        await cog.queue_manager.add_to_queue(GUILD_ID, make_song(index))


@pytest.mark.asyncio
async def test_persistent_playback_failure_gives_up_after_bounded_retries(
    cog: YTMusic,
    ctx: PlaybackContext,
    text_channel: FakeChannel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A song that can never be played must not retry through the whole queue."""
    await _fill_queue(cog, 40)
    attempts = 0

    async def always_failing(*args: Any, **kwargs: Any) -> None:
        nonlocal attempts
        attempts += 1
        if attempts >= SAFETY_CAP:
            cog.queue_manager.clear_queue(GUILD_ID)
        raise RuntimeError("ffmpeg exploded")

    monkeypatch.setattr(cog, "_play_song", always_failing)

    await cog.play_next(ctx)

    assert attempts == MAX_CONSECUTIVE_FAILURES
    failure_embeds = [m.kwargs["embed"].title for m in text_channel.sent]
    assert any("playback_failed_title" in title for title in failure_embeds)


@pytest.mark.asyncio
async def test_failure_counter_resets_after_giving_up(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After giving up, the next request starts with a clean failure budget."""
    await _fill_queue(cog, 10)

    async def always_failing(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(cog, "_play_song", always_failing)
    await cog.play_next(ctx)

    assert cog.state_manager.get_state(GUILD_ID).consecutive_failures == 0


@pytest.mark.asyncio
async def test_successful_playback_resets_the_failure_counter(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One transient failure followed by success leaves no residual count."""
    await _fill_queue(cog, 3)
    state = cog.state_manager.get_state(GUILD_ID)
    outcomes = iter([RuntimeError("transient"), None])

    async def flaky_play_song(
        context: PlaybackContext, song: dict, client: Any
    ) -> None:
        outcome = next(outcomes)
        if outcome is not None:
            raise outcome
        state.consecutive_failures = 0

    monkeypatch.setattr(cog, "_play_song", flaky_play_song)

    await cog.play_next(ctx)

    assert state.consecutive_failures == 0
    assert state.current_song is not None


@pytest.mark.asyncio
async def test_download_failures_are_bounded_too(
    cog: YTMusic,
    ctx: PlaybackContext,
    text_channel: FakeChannel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Songs that keep failing to download must not loop forever."""
    for index in range(40):
        song = make_song(index)
        song.pop("file_path")
        await cog.queue_manager.add_to_queue(GUILD_ID, song)
    downloads = 0

    class FailingYouTube:
        async def download_audio(self, *args: Any, **kwargs: Any) -> tuple:
            nonlocal downloads
            downloads += 1
            if downloads >= SAFETY_CAP:
                cog.queue_manager.clear_queue(GUILD_ID)
            return None, "HTTP 403"

    monkeypatch.setattr(cog, "youtube", FailingYouTube())

    await cog.play_next(ctx)

    assert downloads == MAX_CONSECUTIVE_FAILURES
    assert any(
        "playback_failed_title" in m.kwargs["embed"].title for m in text_channel.sent
    )


@pytest.mark.asyncio
async def test_skip_from_another_voice_channel_is_rejected(
    cog: YTMusic,
    guild: SimpleNamespace,
    text_channel: FakeChannel,
    voice_client: FakeVoiceClient,
) -> None:
    """Only members sitting with the bot may skip its music."""
    voice_client.playing = True
    outsider = make_member(99, voice_channel=object())
    interaction = make_interaction(guild, text_channel, outsider)

    await cog.handle_skip(interaction)

    assert voice_client.stop_calls == 0
    replies = interaction.response.sent + interaction.followup.sent
    assert replies and replies[0]["ephemeral"] is True


@pytest.mark.asyncio
async def test_skip_from_the_same_voice_channel_is_allowed(
    cog: YTMusic,
    guild: SimpleNamespace,
    text_channel: FakeChannel,
    voice_client: FakeVoiceClient,
    requester: SimpleNamespace,
) -> None:
    voice_client.playing = True
    interaction = make_interaction(guild, text_channel, requester)

    await cog.handle_skip(interaction)

    assert voice_client.stop_calls == 1


@pytest.mark.asyncio
async def test_stop_from_outside_any_voice_channel_is_rejected(
    cog: YTMusic,
    guild: SimpleNamespace,
    text_channel: FakeChannel,
    voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True
    lurker = make_member(98, voice_channel=None)
    interaction = make_interaction(guild, text_channel, lurker)

    await cog.handle_stop(interaction)

    assert voice_client.stop_calls == 0
    assert not voice_client.disconnected


@pytest.mark.asyncio
async def test_toggle_playback_from_another_channel_is_rejected(
    cog: YTMusic,
    guild: SimpleNamespace,
    text_channel: FakeChannel,
    voice_client: FakeVoiceClient,
) -> None:
    voice_client.playing = True
    outsider = make_member(99, voice_channel=object())
    cog.ui_manager.get_current_view = lambda guild_id: FakeControlView()
    interaction = make_interaction(guild, text_channel, outsider)

    await cog.handle_toggle_playback(interaction)

    assert voice_client.pause_calls == 0
