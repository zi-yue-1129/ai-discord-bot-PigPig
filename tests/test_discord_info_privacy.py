"""The AI's Discord info tools must not tell anyone what a hidden member is doing."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Optional, Set

import discord
import pytest

from llm.tools.server_context import ServerContextTools
from llm.tools.user_activity import UserActivityTools

GUILD_ID = 42
AUTHOR_ID = 10
HIDDEN_ID = 11


class FakeOptouts:
    def __init__(self, hidden: Set[int], broken: bool = False) -> None:
        self.hidden = hidden
        self.broken = broken

    def _check(self) -> None:
        if self.broken:
            raise RuntimeError("database is locked")

    def is_opted_out(self, guild_id: int, user_id: int) -> bool:
        self._check()
        return guild_id == GUILD_ID and user_id in self.hidden

    def optouts(self, guild_id: int) -> Set[int]:
        self._check()
        return set(self.hidden) if guild_id == GUILD_ID else set()


def _member(member_id: int) -> Any:
    return SimpleNamespace(
        id=member_id,
        bot=False,
        name=f"name{member_id}",
        display_name=f"user{member_id}",
        nick=None,
        joined_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        created_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        roles=[],
        top_role=None,
        status=discord.Status.online,
        desktop_status=discord.Status.online,
        activities=[discord.Game(name="Secret Game")],
    )


def _runtime(store: Optional[FakeOptouts] = None) -> Any:
    members = {member_id: _member(member_id) for member_id in (AUTHOR_ID, HIDDEN_ID)}
    guild = SimpleNamespace(id=GUILD_ID, get_member=members.get)
    channel = SimpleNamespace(name="general", guild=guild, members=list(members.values()))
    message = SimpleNamespace(guild=guild, author=members[AUTHOR_ID], channel=channel)
    store = store if store is not None else FakeOptouts({HIDDEN_ID})
    cogs = {"LeaderboardCog": SimpleNamespace(store=store)}
    return SimpleNamespace(bot=SimpleNamespace(get_cog=cogs.get), message=message, logger=None)


def _info(runtime: Any) -> Any:
    tools = {tool.name: tool for tool in ServerContextTools(runtime).get_tools()}
    return tools["get_user_discord_info"].func


def _channel_context(runtime: Any) -> Any:
    tools = {tool.name: tool for tool in ServerContextTools(runtime).get_tools()}
    return tools["get_channel_context"].func


def _participants(runtime: Any) -> Any:
    return UserActivityTools(runtime).get_tools()[0].func


def test_a_visible_member_still_shows_status_and_activity() -> None:
    reply = _info(_runtime())(user_id=str(AUTHOR_ID))

    assert "Online" in reply and "Secret Game" in reply


def test_a_hidden_member_keeps_status_and_activity_to_themselves() -> None:
    reply = _info(_runtime())(user_id=f"<@{HIDDEN_ID}>")

    assert "user11" in reply
    assert "Secret Game" not in reply and "Online" not in reply and "hidden" in reply


def test_a_hidden_member_asking_about_themselves_gets_it_hidden_too() -> None:
    runtime = _runtime()
    runtime.message.author = runtime.message.guild.get_member(HIDDEN_ID)

    reply = _info(runtime)()

    assert "Secret Game" not in reply and "hidden" in reply


def test_the_info_tool_fails_closed() -> None:
    reply = _info(_runtime(FakeOptouts(set(), broken=True)))(user_id=str(AUTHOR_ID))

    assert "Secret Game" not in reply and "Online" not in reply


def test_hidden_members_are_left_out_of_the_online_list() -> None:
    reply = _participants(_runtime())()

    assert "user10" in reply and "user11" not in reply


def test_the_online_list_fails_closed() -> None:
    reply = _participants(_runtime(FakeOptouts(set(), broken=True)))()

    assert "user10" not in reply and "user11" not in reply


class _TextChannel:
    """Stands in for discord.TextChannel, which cannot be built without a gateway state."""

    def __init__(self, members: list) -> None:
        self.id = 500
        self.name = "general"
        self.category = None
        self.topic = None
        self.nsfw = False
        self.slowmode_delay = 0
        self.members = members


def _online_count(runtime: Any, monkeypatch: pytest.MonkeyPatch) -> Optional[str]:
    monkeypatch.setattr(discord, "TextChannel", _TextChannel)
    runtime.message.channel = _TextChannel(runtime.message.channel.members)
    reply = _channel_context(runtime)()
    found = [line for line in reply.splitlines() if "Online members" in line]
    return found[0] if found else None


def test_the_online_count_does_not_change_with_a_hidden_members_status(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime()
    hidden = runtime.message.guild.get_member(HIDDEN_ID)

    hidden.status = discord.Status.online
    while_online = _online_count(runtime, monkeypatch)
    hidden.status = discord.Status.offline
    while_offline = _online_count(runtime, monkeypatch)

    assert while_online == while_offline == "- Online members with access: ~1"


def test_the_online_count_is_left_out_when_the_opt_outs_cannot_be_read(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _online_count(_runtime(FakeOptouts(set(), broken=True)), monkeypatch) is None


def _without_cog() -> Any:
    return SimpleNamespace(bot=SimpleNamespace(get_cog=lambda name: None))


def test_a_missing_community_database_counts_as_unreadable(tmp_path: Any) -> None:
    from llm.tools.user_stats import _is_hidden, hidden_member_ids

    path = tmp_path / "community.db"

    assert hidden_member_ids(_without_cog(), GUILD_ID, db_path=str(path)) is None
    assert _is_hidden(_without_cog(), GUILD_ID, str(AUTHOR_ID), db_path=str(path)) is True
    assert not path.exists()  # not created empty, which would say nobody is hidden


def test_a_corrupt_community_database_counts_as_unreadable(tmp_path: Any) -> None:
    from llm.tools.user_stats import _is_hidden, hidden_member_ids

    path = tmp_path / "community.db"
    path.write_bytes(b"this is not an sqlite database" * 200)

    assert hidden_member_ids(_without_cog(), GUILD_ID, db_path=str(path)) is None
    assert _is_hidden(_without_cog(), GUILD_ID, str(AUTHOR_ID), db_path=str(path)) is True


def test_the_stored_opt_outs_are_read_without_the_leaderboard_cog(tmp_path: Any) -> None:
    from cogs.community_lib.store import CommunityStore
    from llm.tools.user_stats import hidden_member_ids

    path = str(tmp_path / "community.db")
    CommunityStore(path).set_optout(GUILD_ID, HIDDEN_ID, True)

    assert hidden_member_ids(_without_cog(), GUILD_ID, db_path=path) == {HIDDEN_ID}


# ------------------------------------------------ channels the asker cannot see, and hidden voice members


class _Voice:
    """Stands in for discord.VoiceChannel."""

    def __init__(self, channel_id: int, name: str, members: list, viewers: Optional[Set[int]] = None) -> None:
        self.id = channel_id
        self.name = name
        self.category = None
        self.members = members
        self.bitrate = 64000
        self.user_limit = 0
        self.position = channel_id
        self.viewers = viewers  # None: everyone sees it

    def permissions_for(self, member: Any) -> Any:
        return SimpleNamespace(view_channel=self.viewers is None or member.id in self.viewers)


class _Text(_TextChannel):
    def __init__(self, channel_id: int, name: str, members: list, viewers: Optional[Set[int]] = None) -> None:
        super().__init__(members)
        self.id = channel_id
        self.name = name
        self.topic = f"topic of {name}"
        self.position = channel_id
        self.viewers = viewers

    def permissions_for(self, member: Any) -> Any:
        return SimpleNamespace(view_channel=self.viewers is None or member.id in self.viewers)


def _guild_with(monkeypatch: pytest.MonkeyPatch, runtime: Any, *channels: Any) -> Any:
    monkeypatch.setattr(discord, "TextChannel", _Text)
    monkeypatch.setattr(discord, "VoiceChannel", _Voice)
    guild = runtime.message.guild
    guild.channels = list(channels)
    guild.name, guild.member_count, guild.premium_tier, guild.premium_subscription_count = "Pig Land", 2, 0, 0
    guild.owner, guild.created_at, guild.roles = None, None, []
    return guild


def _server_context(runtime: Any) -> Any:
    tools = {tool.name: tool for tool in ServerContextTools(runtime).get_tools()}
    return tools["get_server_context"].func


def test_a_voice_channel_the_asker_cannot_see_is_reported_as_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime()
    members = list(runtime.message.channel.members)
    _guild_with(monkeypatch, runtime, _Voice(700, "secret-room", members, viewers={HIDDEN_ID}))

    reply = _channel_context(runtime)("secret-room")

    assert reply == "Channel 'secret-room' not found in this server."


def test_a_text_channel_the_asker_cannot_see_is_reported_as_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime()
    _guild_with(monkeypatch, runtime, _Text(701, "staff", list(runtime.message.channel.members), viewers={HIDDEN_ID}))

    assert _channel_context(runtime)("staff") == "Channel 'staff' not found in this server."


def test_a_name_shared_with_a_private_channel_finds_the_one_the_asker_can_see(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime()
    members = list(runtime.message.channel.members)
    _guild_with(monkeypatch, runtime, _Text(701, "chat", members, viewers={HIDDEN_ID}), _Text(702, "chat", members))

    assert "ID: 702" in _channel_context(runtime)("chat")


def test_the_server_overview_lists_only_channels_the_asker_can_see(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime()
    members = list(runtime.message.channel.members)
    _guild_with(
        monkeypatch, runtime,
        _Text(701, "public-chat", members), _Text(702, "staff-only", members, viewers={HIDDEN_ID}),
        _Voice(703, "lounge", members), _Voice(704, "secret-room", members, viewers={HIDDEN_ID}),
    )

    reply = _server_context(runtime)()

    assert "public-chat" in reply and "lounge" in reply
    assert "staff-only" not in reply and "secret-room" not in reply


def test_a_visible_voice_channel_leaves_hidden_members_out_of_its_names_and_count(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime()
    members = list(runtime.message.channel.members)  # user10 and the hidden user11
    _guild_with(monkeypatch, runtime, _Voice(703, "lounge", members))

    reply = _channel_context(runtime)("lounge")

    assert "user10" in reply and "user11" not in reply and "Connected: 1 users" in reply


def test_a_voice_channel_shows_nobody_when_the_opt_outs_cannot_be_read(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime(FakeOptouts(set(), broken=True))
    members = list(runtime.message.channel.members)
    _guild_with(monkeypatch, runtime, _Voice(703, "lounge", members))

    reply = _channel_context(runtime)("lounge")

    assert "user10" not in reply and "user11" not in reply and "Connected" not in reply


def test_the_voice_participant_list_leaves_hidden_members_out(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime()
    _guild_with(monkeypatch, runtime)
    runtime.message.channel = _Voice(703, "lounge", list(runtime.message.channel.members))
    runtime.message.channel.guild = runtime.message.guild

    reply = _participants(runtime)()

    assert "user10" in reply and "user11" not in reply


def test_the_voice_participant_list_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = _runtime(FakeOptouts(set(), broken=True))
    _guild_with(monkeypatch, runtime)
    runtime.message.channel = _Voice(703, "lounge", list(runtime.message.channel.members))
    runtime.message.channel.guild = runtime.message.guild

    reply = _participants(runtime)()

    assert "user10" not in reply and "user11" not in reply
