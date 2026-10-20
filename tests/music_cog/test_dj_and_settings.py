"""Server music settings: the DJ role, vote skipping, 24/7, the default volume and their storage."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, List

import pytest
from music_cog.helpers import GUILD_ID, REQUESTER_ID, make_member, make_song

from cogs.music import YTMusic
from cogs.music_lib.context import PlaybackContext
from cogs.music_lib.music_store import GuildMusicSettings, MusicStore

DJ_ROLE = 555


@pytest.fixture
def voice_channel() -> SimpleNamespace:
    """A voice channel that knows who is in it (overrides the plain one from conftest)."""
    return SimpleNamespace(name="vc", members=[])


def _join(voice_channel: SimpleNamespace, *user_ids: int, roles: tuple = (), manager: bool = False) -> List[Any]:
    members = []
    for user_id in user_ids:
        member = make_member(user_id, voice_channel)
        member.bot = False
        member.roles = [SimpleNamespace(id=role) for role in roles]
        member.guild_permissions = SimpleNamespace(administrator=False, manage_guild=manager)
        voice_channel.members.append(member)
        members.append(member)
    return members


def _ctx(ctx: PlaybackContext, user: Any) -> PlaybackContext:
    return PlaybackContext(guild=ctx.guild, channel=ctx.channel, user=user)


def _playing(cog: YTMusic, voice_client: Any, added_by: int = REQUESTER_ID) -> None:
    cog.state_manager.update_state(GUILD_ID, current_song=make_song(1, added_by=added_by))
    voice_client.playing = True


# ------------------------------------------------------------------ the store


def test_settings_default_and_survive_a_restart(tmp_path) -> None:
    store = MusicStore(tmp_path / "music.db")
    assert store.get_settings(GUILD_ID) == GuildMusicSettings()

    store.update_settings(GUILD_ID, dj_role_id=DJ_ROLE, stay_247=True, stay_channel_id=9, default_volume=40)

    reopened = MusicStore(tmp_path / "music.db").get_settings(GUILD_ID)
    assert (reopened.dj_role_id, reopened.stay_247, reopened.default_volume) == (DJ_ROLE, True, 40)
    assert MusicStore(tmp_path / "music.db").guilds_staying() == {GUILD_ID: 9}
    assert reopened.to_dict()["dj_role_id"] == str(DJ_ROLE)


def test_an_unknown_setting_is_refused(tmp_path) -> None:
    with pytest.raises(ValueError):
        MusicStore(tmp_path / "music.db").update_settings(GUILD_ID, volume=3)


# ------------------------------------------------------------------ DJ role


@pytest.mark.asyncio
async def test_without_a_dj_role_everyone_in_the_channel_may_control(cog, ctx, voice_channel, voice_client) -> None:
    listener, _ = _join(voice_channel, 50, 51)
    _playing(cog, voice_client)

    result = await cog.service.pause(_ctx(ctx, listener))

    assert result.ok


@pytest.mark.asyncio
async def test_with_a_dj_role_only_djs_may_pause(cog, ctx, voice_channel, voice_client) -> None:
    cog.store.update_settings(GUILD_ID, dj_role_id=DJ_ROLE)
    listener, _ = _join(voice_channel, 50, 51)
    (dj,) = _join(voice_channel, 52, roles=(DJ_ROLE,))
    _playing(cog, voice_client)

    refused = await cog.service.pause(_ctx(ctx, listener))
    allowed = await cog.service.pause(_ctx(ctx, dj))

    assert refused.reason == "dj_only"
    assert allowed.ok


@pytest.mark.asyncio
async def test_server_managers_and_lonely_listeners_count_as_djs(cog, ctx, voice_channel, voice_client) -> None:
    cog.store.update_settings(GUILD_ID, dj_role_id=DJ_ROLE)
    (manager,) = _join(voice_channel, 60, manager=True)
    assert cog.service.is_dj(_ctx(ctx, manager))

    voice_channel.members.clear()
    (alone,) = _join(voice_channel, 61)
    assert cog.service.is_dj(_ctx(ctx, alone))


@pytest.mark.asyncio
async def test_a_listener_skips_by_vote_when_a_dj_role_is_set(cog, ctx, voice_channel, voice_client) -> None:
    cog.store.update_settings(GUILD_ID, dj_role_id=DJ_ROLE, vote_ratio=0.5)
    first, second, _ = _join(voice_channel, 70, 71, 72)
    _playing(cog, voice_client)

    vote = await cog.service.skip(_ctx(ctx, first))
    again = await cog.service.skip(_ctx(ctx, first))
    skip = await cog.service.skip(_ctx(ctx, second))

    assert vote.data == {"voted": True, "votes": 1, "required": 2, "title": "song 1"}
    assert again.data["votes"] == 1  # one vote per person
    assert voice_client.stop_calls == 1 and skip.data.get("voted") is None


@pytest.mark.asyncio
async def test_the_requester_skips_their_own_song_without_a_vote(cog, ctx, voice_channel, voice_client) -> None:
    cog.store.update_settings(GUILD_ID, dj_role_id=DJ_ROLE)
    requester, _ = _join(voice_channel, 80, 81)
    _playing(cog, voice_client, added_by=80)

    result = await cog.service.skip(_ctx(ctx, requester))

    assert result.ok and not result.data.get("voted")
    assert voice_client.stop_calls == 1


@pytest.mark.asyncio
async def test_a_listener_may_remove_only_their_own_queued_songs(cog, ctx, voice_channel, voice_client) -> None:
    cog.store.update_settings(GUILD_ID, dj_role_id=DJ_ROLE)
    owner, other = _join(voice_channel, 90, 91)
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(1, added_by=90))
    await cog.queue_manager.add_to_queue(GUILD_ID, make_song(2, added_by=90))

    refused = await cog.service.remove_from_queue(_ctx(ctx, other), 1)
    removed = await cog.service.remove_from_queue(_ctx(ctx, owner), 1)

    assert refused.reason == "not_your_song"
    assert removed.ok and removed.data["title"] == "song 1"


# ------------------------------------------------------------- 24/7 & volume


@pytest.mark.asyncio
async def test_24_7_mode_starts_no_idle_disconnect(cog) -> None:
    cog.store.update_settings(GUILD_ID, stay_247=True)

    await cog._start_disconnect_timer(GUILD_ID, 5)

    assert GUILD_ID not in cog.disconnect_timers


@pytest.mark.asyncio
async def test_a_new_session_starts_at_the_default_volume(cog) -> None:
    cog.store.update_settings(GUILD_ID, default_volume=35)

    cog._start_session(GUILD_ID)
    cog.state_manager.get_state(GUILD_ID).volume = 0.9
    cog._start_session(GUILD_ID)  # later songs keep the volume the listeners chose

    assert cog.state_manager.get_state(GUILD_ID).volume == 0.9
    await cog._cleanup_voice_session(GUILD_ID)
    cog._start_session(GUILD_ID)
    assert cog.state_manager.get_state(GUILD_ID).volume == 0.35


@pytest.mark.asyncio
async def test_the_bot_rejoins_its_24_7_channel_after_a_restart(cog, monkeypatch) -> None:
    joined: List[Any] = []
    channel = SimpleNamespace(id=33)
    guild = SimpleNamespace(id=GUILD_ID, voice_client=None, get_channel=lambda channel_id: channel if channel_id == 33 else None)
    cog.bot.get_guild = lambda guild_id: guild
    cog.store.update_settings(GUILD_ID, stay_247=True, stay_channel_id=33)

    async def stay_in(target_guild: Any, target: Any) -> bool:
        joined.append(target)
        return True

    monkeypatch.setattr(cog, "stay_in", stay_in)
    await cog.on_ready()

    assert joined == [channel]
