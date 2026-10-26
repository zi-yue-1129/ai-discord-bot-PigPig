"""The AI's Discord info tools must not tell anyone what a hidden member is doing."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Optional, Set

import discord

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
