"""When nobody is left in the voice channel the bot leaves and takes its player panel with it."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, List

import pytest
from music_cog.helpers import GUILD_ID, FakeMessage, FakeVoiceClient, make_song

import cogs.music as music_module
from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext


@pytest.fixture
def room(guild: SimpleNamespace, voice_client: FakeVoiceClient) -> SimpleNamespace:
    """The bot's voice channel; members are added by the tests."""
    channel = SimpleNamespace(members=[])
    voice_client.channel = channel
    return channel


@pytest.fixture
def wired_player(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> List[Any]:
    """Replaces audio, UI and the player loop with fakes, so a song can be started offline."""
    loops: List[dict] = []

    def fake_source(song: dict, volume: float = 1.0, start_offset: float = 0.0) -> str:
        return "source"

    async def fake_ui(*args: Any, **kwargs: Any) -> None:
        return None

    def fake_loop(ctx: Any, song: dict, start_offset: float = 0.0) -> Any:
        loops.append(song)
        return asyncio.sleep(0)

    monkeypatch.setattr(cog.audio_manager, "create_audio_source", fake_source)
    monkeypatch.setattr(cog.ui_manager, "update_player_ui", fake_ui, raising=False)
    monkeypatch.setattr(cog, "_player_loop", fake_loop)
    return loops


@pytest.fixture
def timers(cog: YTMusic, monkeypatch: pytest.MonkeyPatch) -> List[tuple]:
    """Records the disconnect timers that get started instead of sleeping through them."""
    started: List[tuple] = []

    async def record(guild_id: int, delay: float = music_module.PAUSED_DISCONNECT_SECONDS) -> None:
        started.append((guild_id, delay))
        cog.disconnect_timers[guild_id] = SimpleNamespace(cancel=lambda: None, done=lambda: False)

    monkeypatch.setattr(cog, "_start_disconnect_timer", record)
    return started


async def _last_person_leaves(cog: YTMusic, guild: SimpleNamespace, room: SimpleNamespace) -> None:
    leaver = SimpleNamespace(id=5, bot=False, guild=guild)
    event = SimpleNamespace(channel=room)
    await cog.on_voice_state_update(leaver, event, event)


# ------------------------------------------------------------ the room empties


@pytest.mark.asyncio
async def test_a_playing_song_is_paused_and_the_bot_leaves_soon(
    cog: YTMusic, guild: SimpleNamespace, voice_client: FakeVoiceClient, room: SimpleNamespace, timers: List[tuple]
) -> None:
    voice_client.playing = True

    await _last_person_leaves(cog, guild, room)

    assert voice_client.pause_calls == 1
    assert timers == [(GUILD_ID, music_module.EMPTY_CHANNEL_DISCONNECT_SECONDS)]
    assert music_module.EMPTY_CHANNEL_DISCONNECT_SECONDS <= 120


@pytest.mark.asyncio
async def test_the_bot_still_leaves_when_the_room_empties_between_two_songs(
    cog: YTMusic, guild: SimpleNamespace, voice_client: FakeVoiceClient, room: SimpleNamespace, timers: List[tuple]
) -> None:
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(0))

    await _last_person_leaves(cog, guild, room)

    assert timers == [(GUILD_ID, music_module.EMPTY_CHANNEL_DISCONNECT_SECONDS)]


@pytest.mark.asyncio
async def test_the_bot_still_leaves_when_the_room_empties_while_a_user_has_the_song_paused(
    cog: YTMusic, guild: SimpleNamespace, voice_client: FakeVoiceClient, room: SimpleNamespace, timers: List[tuple]
) -> None:
    voice_client.paused = True

    await _last_person_leaves(cog, guild, room)

    assert timers == [(GUILD_ID, music_module.EMPTY_CHANNEL_DISCONNECT_SECONDS)]
    assert voice_client.pause_calls == 0


@pytest.mark.asyncio
async def test_a_timer_that_is_already_running_is_not_postponed(
    cog: YTMusic, guild: SimpleNamespace, voice_client: FakeVoiceClient, room: SimpleNamespace, timers: List[tuple]
) -> None:
    voice_client.paused = True
    cog.disconnect_timers[GUILD_ID] = SimpleNamespace(cancel=lambda: None, done=lambda: False)

    await _last_person_leaves(cog, guild, room)

    assert timers == []


@pytest.mark.asyncio
async def test_someone_still_in_the_room_keeps_the_music_going(
    cog: YTMusic, guild: SimpleNamespace, voice_client: FakeVoiceClient, room: SimpleNamespace, timers: List[tuple]
) -> None:
    voice_client.playing = True
    room.members.append(SimpleNamespace(id=6, bot=False))

    await _last_person_leaves(cog, guild, room)

    assert voice_client.pause_calls == 0
    assert timers == []


@pytest.mark.asyncio
async def test_a_song_that_starts_in_an_empty_room_is_paused_and_the_bot_leaves_soon(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, room: SimpleNamespace,
    timers: List[tuple], wired_player: List[Any],
) -> None:
    await cog._play_song(ctx, make_song(1), voice_client)

    assert voice_client.pause_calls == 1
    assert cog.state_manager.get_state(GUILD_ID).auto_paused is True
    assert timers == [(GUILD_ID, music_module.EMPTY_CHANNEL_DISCONNECT_SECONDS)]


@pytest.mark.asyncio
async def test_the_timer_disconnects_even_when_a_song_is_somehow_playing_in_an_empty_room(
    cog: YTMusic, voice_client: FakeVoiceClient, room: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    cleaned: List[int] = []

    async def cleanup(guild_id: int) -> None:
        cleaned.append(guild_id)

    monkeypatch.setattr(cog, "_cleanup_voice_session", cleanup)
    voice_client.playing = True

    await cog._disconnect_after_delay(GUILD_ID, 0)

    assert cleaned == [GUILD_ID]


@pytest.mark.asyncio
async def test_the_timer_does_not_disconnect_a_song_that_has_listeners(
    cog: YTMusic, voice_client: FakeVoiceClient, room: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    cleaned: List[int] = []

    async def cleanup(guild_id: int) -> None:
        cleaned.append(guild_id)

    monkeypatch.setattr(cog, "_cleanup_voice_session", cleanup)
    voice_client.playing = True
    room.members.append(SimpleNamespace(id=6, bot=False))

    await cog._disconnect_after_delay(GUILD_ID, 0)

    assert cleaned == []


# ------------------------------------------------------------------ the panel


class _Panel(FakeMessage):
    """A player panel message that remembers it was deleted."""


@pytest.mark.asyncio
async def test_leaving_removes_the_panel_even_after_the_progress_updater_re_posted_it(
    cog: YTMusic, voice_client: FakeVoiceClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = _Panel()
    reposted = _Panel()
    cog.state_manager.update_state(GUILD_ID, ui_messages=[original], current_message=original)
    # The progress updater posts a fresh panel every 10 minutes and only tracks it on the view.
    view = SimpleNamespace(message=reposted, stop_progress_updater=lambda: None)
    cog.ui_manager.get_current_view = lambda guild_id: view
    monkeypatch.setattr(cog, "get_voice_client", lambda guild_id: voice_client)

    async def no_files(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(cog.audio_manager, "cleanup_guild_files", no_files)
    monkeypatch.setattr(cog.prefetcher, "cancel", no_files)

    await cog._cleanup_voice_session(GUILD_ID)

    assert original.deleted is True
    assert reposted.deleted is True


@pytest.mark.asyncio
async def test_leaving_without_a_panel_does_not_fail(
    cog: YTMusic, voice_client: FakeVoiceClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cog, "get_voice_client", lambda guild_id: voice_client)

    async def no_files(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(cog.audio_manager, "cleanup_guild_files", no_files)
    monkeypatch.setattr(cog.prefetcher, "cancel", no_files)

    await cog._cleanup_voice_session(GUILD_ID)

    assert voice_client.disconnected is True
