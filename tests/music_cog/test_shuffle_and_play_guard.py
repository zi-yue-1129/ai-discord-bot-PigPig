"""Tests for whole-list shuffle, the /play voice-channel check and two smaller voice fixes."""

from __future__ import annotations

import asyncio
import random
from types import SimpleNamespace
from typing import Any, List

import pytest
from music_cog.helpers import (
    GUILD_ID,
    REQUESTER_ID,
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

SEED = 20261011


def _titles(cog: YTMusic) -> List[str]:
    return [song["title"] for song in cog.queue_manager.get_queue_snapshot(GUILD_ID)]


async def _fill(cog: YTMusic, count: int) -> List[str]:
    for index in range(count):
        await cog.queue_manager.add_to_queue(GUILD_ID, make_song(index))
    return _titles(cog)


def _expected_order(titles: List[str]) -> List[str]:
    shuffled = list(titles)
    random.Random(SEED).shuffle(shuffled)
    return shuffled


# ----------------------------------------------------------------------- shuffle


@pytest.mark.asyncio
async def test_turning_shuffle_on_shuffles_the_whole_queue(cog: YTMusic) -> None:
    original = await _fill(cog, 12)
    cog.queue_manager._rng = random.Random(SEED)

    cog.queue_manager.toggle_shuffle(GUILD_ID)

    assert _titles(cog) == _expected_order(original)
    assert _titles(cog) != original


@pytest.mark.asyncio
async def test_turning_shuffle_off_keeps_the_order(cog: YTMusic) -> None:
    await _fill(cog, 12)
    cog.queue_manager.toggle_shuffle(GUILD_ID)
    shuffled = _titles(cog)

    cog.queue_manager.toggle_shuffle(GUILD_ID)

    assert _titles(cog) == shuffled


def test_turning_shuffle_on_shuffles_the_buffered_playlist(cog: YTMusic) -> None:
    songs = [make_song(index) for index in range(10)]
    cog.queue_manager.set_playlist(GUILD_ID, list(songs))
    cog.queue_manager._rng = random.Random(SEED)

    cog.queue_manager.toggle_shuffle(GUILD_ID)

    titles = [song["title"] for song in cog.queue_manager.guild_playlists[GUILD_ID]]
    assert sorted(titles) == sorted(song["title"] for song in songs)
    assert titles == _expected_order([song["title"] for song in songs])


@pytest.mark.asyncio
async def test_a_playlist_added_while_shuffle_is_on_is_shuffled(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeYouTube()
    monkeypatch.setattr(cog, "youtube", fake)
    cog.queue_manager.toggle_shuffle(GUILD_ID)
    cog.queue_manager._rng = random.Random(SEED)

    added, total, failure = await cog.service.enqueue_playlist(ctx, "https://youtube.com/playlist?list=PL1")

    assert failure is None
    assert total == 8
    original = [song["title"] for song in fake.playlist]
    shuffled = _expected_order(original)
    buffered = [song["title"] for song in cog.queue_manager.guild_playlists[GUILD_ID]]
    assert [song["title"] for song in added or []] == shuffled[: len(added or [])]
    assert buffered == shuffled[len(added or []):]


@pytest.mark.asyncio
async def test_with_shuffle_a_finished_song_waits_for_the_next_round_instead_of_rejoining_the_queue(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def no_next(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(cog, "play_next", no_next)
    cog.queue_manager.set_play_mode(GUILD_ID, PlayMode.LOOP_QUEUE)
    cog.queue_manager.toggle_shuffle(GUILD_ID)
    song = make_song(1)
    cog.state_manager.update_state(GUILD_ID, current_song=song)

    await cog._handle_after_play(ctx, song)

    assert _titles(cog) == []
    assert cog.queue_manager.guild_finished[GUILD_ID] == [song]


@pytest.mark.asyncio
async def test_without_shuffle_a_finished_song_still_rejoins_the_end_of_the_queue(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def no_next(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(cog, "play_next", no_next)
    cog.queue_manager.set_play_mode(GUILD_ID, PlayMode.LOOP_QUEUE)
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(2))
    song = make_song(1)
    cog.state_manager.update_state(GUILD_ID, current_song=song)

    await cog._handle_after_play(ctx, song)

    assert _titles(cog) == ["song 2", "song 1"]


@pytest.mark.asyncio
async def test_with_autoplay_a_finished_song_does_not_play_again_before_the_recommendations(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def no_next(*args: Any, **kwargs: Any) -> None:
        return None

    async def recommend(_ctx: PlaybackContext, guild_id: int, notify: bool = False) -> int:
        for index in (2, 3):
            await cog.queue_manager.add_to_queue(guild_id, make_song(index))
        return 2

    monkeypatch.setattr(cog, "play_next", no_next)
    monkeypatch.setattr(cog, "_trigger_autoplay", recommend)
    cog.queue_manager.set_play_mode(GUILD_ID, PlayMode.LOOP_QUEUE)
    song = make_song(1)
    cog.state_manager.update_state(GUILD_ID, current_song=song, autoplay=True)

    await cog._handle_after_play(ctx, song)

    assert _titles(cog) == ["song 2", "song 3", "song 1"]


@pytest.mark.asyncio
async def test_after_a_skip_in_loop_queue_with_autoplay_the_next_song_is_a_recommendation(
    cog: YTMusic, ctx: PlaybackContext, voice_client: FakeVoiceClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    played: List[str] = []

    async def play(_ctx: PlaybackContext, song: dict, _voice_client: Any) -> None:
        played.append(song["title"])

    async def recommend(_ctx: PlaybackContext, guild_id: int, notify: bool = False) -> int:
        for index in (2, 3):
            await cog.queue_manager.add_to_queue(guild_id, make_song(index) | {"stream_url": "https://stream"})
        return 2

    monkeypatch.setattr(cog, "_play_song", play)
    monkeypatch.setattr(cog, "_trigger_autoplay", recommend)
    cog.queue_manager.set_play_mode(GUILD_ID, PlayMode.LOOP_QUEUE)
    song = make_song(1) | {"stream_url": "https://stream"}
    cog.state_manager.update_state(GUILD_ID, current_song=song, autoplay=True, force_next=True)

    await cog._handle_after_play(ctx, song)

    assert played == ["song 2"]
    assert _titles(cog) == ["song 3", "song 1"]


@pytest.mark.asyncio
async def test_a_finished_song_stays_in_the_loop_when_the_recommendations_fail(
    cog: YTMusic, ctx: PlaybackContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def no_next(*args: Any, **kwargs: Any) -> None:
        return None

    async def fail(*args: Any, **kwargs: Any) -> int:
        raise RuntimeError("recommender is down")

    monkeypatch.setattr(cog, "play_next", no_next)
    monkeypatch.setattr(cog, "_trigger_autoplay", fail)
    cog.queue_manager.set_play_mode(GUILD_ID, PlayMode.LOOP_QUEUE)
    song = make_song(1)
    cog.state_manager.update_state(GUILD_ID, current_song=song, autoplay=True)

    await cog._handle_after_play(ctx, song)

    assert _titles(cog) == ["song 1"]


@pytest.mark.asyncio
async def test_when_the_round_ends_every_song_comes_back_once_in_a_new_order(
    cog: YTMusic, ctx: PlaybackContext
) -> None:
    cog.queue_manager.set_play_mode(GUILD_ID, PlayMode.LOOP_QUEUE)
    cog.queue_manager.toggle_shuffle(GUILD_ID)
    cog.queue_manager._rng = random.Random(SEED)
    songs = [make_song(index) for index in range(10)]
    for song in songs:
        cog.queue_manager.finish_for_cycle(GUILD_ID, song)

    next_song = await cog._get_next_song(ctx, GUILD_ID, force_new=False)

    remaining = [next_song["title"]] + _titles(cog)
    assert sorted(remaining) == sorted(song["title"] for song in songs)
    assert remaining != [song["title"] for song in songs]


@pytest.mark.asyncio
async def test_clearing_the_queue_forgets_the_songs_of_the_current_round(cog: YTMusic) -> None:
    cog.queue_manager.finish_for_cycle(GUILD_ID, make_song(1))

    cog.queue_manager.clear_queue(GUILD_ID)

    assert cog.queue_manager.guild_finished.get(GUILD_ID, []) == []


# ------------------------------------------------------------------ /play check


class _Response:
    """An interaction response that records what was sent and deferred."""

    def __init__(self) -> None:
        self.sent: List[dict] = []
        self.deferred = False
        self.done = False

    def is_done(self) -> bool:
        return self.done

    async def send_message(self, *args: Any, **kwargs: Any) -> None:
        self.done = True
        self.sent.append({"args": args, **kwargs})

    async def defer(self, *args: Any, **kwargs: Any) -> None:
        self.deferred = True
        self.done = True


def _play_interaction(guild: SimpleNamespace, channel: FakeChannel, user: SimpleNamespace) -> SimpleNamespace:
    interaction = make_interaction(guild, channel, user)
    interaction.response = _Response()
    interaction.edits = []

    async def edit(**kwargs: Any) -> None:
        interaction.edits.append(kwargs)

    interaction.edit_original_response = edit
    return interaction


@pytest.mark.asyncio
async def test_play_is_refused_to_someone_outside_the_channel_where_music_is_playing(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, voice_client: FakeVoiceClient
) -> None:
    voice_client.playing = True
    outsider = make_member(99, voice_channel=object())
    interaction = _play_interaction(guild, text_channel, outsider)

    await cog.play.callback(cog, interaction, "怪物")

    assert interaction.response.sent
    assert interaction.response.deferred is False
    assert cog.queue_manager.get_queue_snapshot(GUILD_ID) == []


@pytest.mark.asyncio
async def test_play_is_refused_while_the_player_is_paused_too(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, voice_client: FakeVoiceClient
) -> None:
    voice_client.paused = True
    outsider = make_member(99, voice_channel=object())
    interaction = _play_interaction(guild, text_channel, outsider)

    await cog.play.callback(cog, interaction, None)

    assert interaction.response.sent
    assert interaction.response.deferred is False


@pytest.mark.asyncio
async def test_an_idle_bot_follows_the_requester_into_their_channel(
    cog: YTMusic, guild: SimpleNamespace, text_channel: FakeChannel, voice_client: FakeVoiceClient
) -> None:
    other_channel = object()
    requester = make_member(REQUESTER_ID, voice_channel=other_channel)
    interaction = _play_interaction(guild, text_channel, requester)

    await cog.play.callback(cog, interaction, None)

    assert voice_client.moved_to is other_channel
    assert interaction.response.deferred is True


# ---------------------------------------------------------------- voice fixes


def _voice_event(channel: object) -> tuple:
    return SimpleNamespace(channel=channel), SimpleNamespace(channel=channel)


def _human(user_id: int) -> SimpleNamespace:
    return SimpleNamespace(id=user_id, bot=False)


@pytest.fixture
def room(guild: SimpleNamespace, voice_client: FakeVoiceClient) -> SimpleNamespace:
    """The bot's voice channel with a mutable member list."""
    channel = SimpleNamespace(members=[])
    voice_client.channel = channel
    return channel


@pytest.mark.asyncio
async def test_a_player_the_bot_paused_because_the_room_emptied_resumes_when_someone_joins(
    cog: YTMusic, guild: SimpleNamespace, voice_client: FakeVoiceClient, room: SimpleNamespace
) -> None:
    voice_client.playing = True
    leaver = SimpleNamespace(id=5, bot=False, guild=guild)
    before, after = _voice_event(room)

    await cog.on_voice_state_update(leaver, before, after)
    assert voice_client.pause_calls == 1
    room.members.append(_human(6))
    await cog.on_voice_state_update(SimpleNamespace(id=6, bot=False, guild=guild), before, after)

    assert voice_client.resume_calls == 1
    assert GUILD_ID not in cog.disconnect_timers


@pytest.mark.asyncio
async def test_a_song_the_user_paused_stays_paused_when_someone_joins(
    cog: YTMusic, ctx: PlaybackContext, guild: SimpleNamespace, voice_client: FakeVoiceClient,
    room: SimpleNamespace,
) -> None:
    voice_client.playing = True
    ctx.user.voice = SimpleNamespace(channel=room)
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(0))
    paused = await cog.service.pause(ctx)
    assert paused.ok
    idle_timer = cog.disconnect_timers[GUILD_ID]
    room.members.append(_human(6))
    before, after = _voice_event(room)

    await cog.on_voice_state_update(SimpleNamespace(id=6, bot=False, guild=guild), before, after)
    idle_timer.cancel()

    assert voice_client.resume_calls == 0


@pytest.mark.asyncio
async def test_the_idle_disconnect_still_announces_itself_when_the_bots_own_disconnect_cancels_timers(
    cog: YTMusic, text_channel: FakeChannel, voice_client: FakeVoiceClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    cog.state_manager.update_state(GUILD_ID, current_message=SimpleNamespace(channel=text_channel))

    async def cleanup_that_triggers_the_voice_state_handler(guild_id: int) -> None:
        # The bot leaving fires on_voice_state_update, which cancels the guild's timer.
        await cog._cancel_disconnect_timer(guild_id)
        await asyncio.sleep(0)

    monkeypatch.setattr(cog, "_cleanup_voice_session", cleanup_that_triggers_the_voice_state_handler)
    voice_client.paused = True
    timer = asyncio.get_running_loop().create_task(cog._disconnect_after_delay(GUILD_ID, 0))
    cog.disconnect_timers[GUILD_ID] = timer

    await timer

    assert any("idle_disconnect" in str(m.kwargs["embed"].title) for m in text_channel.sent)
