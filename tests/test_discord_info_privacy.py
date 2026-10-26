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

    def read_optouts(self, guild_id: int) -> Set[int]:
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


def _with_store(store: Any) -> Any:
    return SimpleNamespace(bot=SimpleNamespace(get_cog=lambda name: SimpleNamespace(store=store)))


def test_a_lost_database_behind_a_loaded_cog_counts_as_unreadable(tmp_path: Any) -> None:
    from cogs.community_lib.store import CommunityStore
    from llm.tools.user_stats import _is_hidden, hidden_member_ids

    path = tmp_path / "community.db"
    store = CommunityStore(path)  # the cog is loaded, the file was never created (or was lost)

    assert hidden_member_ids(_with_store(store), GUILD_ID) is None
    assert _is_hidden(_with_store(store), GUILD_ID, str(AUTHOR_ID)) is True
    assert not path.exists()


def test_a_database_deleted_after_use_counts_as_unreadable(tmp_path: Any) -> None:
    from cogs.community_lib.store import CommunityStore
    from llm.tools.user_stats import hidden_member_ids

    path = tmp_path / "community.db"
    store = CommunityStore(path)
    store.set_optout(GUILD_ID, HIDDEN_ID, True)
    assert hidden_member_ids(_with_store(store), GUILD_ID) == {HIDDEN_ID}
    path.unlink()

    assert hidden_member_ids(_with_store(store), GUILD_ID) is None
    assert hidden_member_ids(_without_cog(), GUILD_ID, db_path=str(path)) is None
    assert not path.exists()


def test_an_empty_database_file_counts_as_unreadable(tmp_path: Any) -> None:
    from llm.tools.user_stats import hidden_member_ids

    path = tmp_path / "community.db"
    path.write_bytes(b"")

    assert hidden_member_ids(_without_cog(), GUILD_ID, db_path=str(path)) is None
    assert path.stat().st_size == 0  # not initialised into an empty opt-out list


def test_a_locked_database_counts_as_unreadable(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    import sqlite3

    from cogs.community_lib import store as store_module
    from cogs.community_lib.store import CommunityStore
    from llm.tools.user_stats import hidden_member_ids

    path = tmp_path / "community.db"
    store = CommunityStore(path)
    store.set_optout(GUILD_ID, HIDDEN_ID, True)
    monkeypatch.setattr(store_module, "OPTOUT_READ_TIMEOUT", 0.1)
    holder = sqlite3.connect(path)
    try:
        holder.execute("BEGIN EXCLUSIVE")
        assert hidden_member_ids(_with_store(store), GUILD_ID) is None
    finally:
        holder.rollback()
        holder.close()


def test_a_healthy_empty_opt_out_list_shows_everyone(tmp_path: Any) -> None:
    from cogs.community_lib.store import CommunityStore
    from llm.tools.user_stats import hidden_member_ids

    store = CommunityStore(tmp_path / "community.db")
    store.set_optout(GUILD_ID, HIDDEN_ID, False)  # creates the tables, hides nobody
    runtime = _runtime(store)

    assert hidden_member_ids(runtime, GUILD_ID) == set()
    assert "Secret Game" in _info(runtime)(user_id=str(HIDDEN_ID))
    assert "user11" in _participants(runtime)()


def test_an_opt_out_list_of_none_hides_everyone() -> None:
    class ReturnsNone:
        def read_optouts(self, guild_id: int) -> None:
            return None

    runtime = _runtime(ReturnsNone())  # type: ignore[arg-type]

    assert "Secret Game" not in _info(runtime)(user_id=str(AUTHOR_ID))
    assert "user10" not in _participants(runtime)()
