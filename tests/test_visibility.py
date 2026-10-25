"""addons.visibility with real discord.py guilds, roles, overwrites and threads."""

from __future__ import annotations

from typing import Any, List, Optional
from unittest.mock import MagicMock

import discord
from discord.state import ConnectionState
from discord.threads import ThreadMember

from addons.visibility import audience_can_read, can_read

GUILD_ID = 1
VIEW_AND_HISTORY = discord.Permissions(view_channel=True, read_message_history=True, send_messages=True)
HISTORY = discord.Permissions(read_message_history=True)
VIEW = discord.Permissions(view_channel=True)


def _role(role_id: int, permissions: discord.Permissions, position: int) -> dict:
    return {
        "id": role_id, "name": f"r{role_id}", "permissions": str(permissions.value), "position": position,
        "color": 0, "hoist": False, "managed": False, "mentionable": False,
    }


def _member(user_id: int, roles: List[int] = ()) -> dict:
    return {
        "user": {"id": user_id, "username": f"u{user_id}", "discriminator": "0", "avatar": None},
        "roles": [str(r) for r in roles], "joined_at": "2020-01-01T00:00:00+00:00", "deaf": False, "mute": False, "flags": 0,
    }


def _overwrite(target: int, kind: int, allow: discord.Permissions = discord.Permissions.none(), deny: discord.Permissions = discord.Permissions.none()) -> dict:
    return {"id": str(target), "type": kind, "allow": str(allow.value), "deny": str(deny.value)}


def _guild(
    everyone: discord.Permissions = VIEW_AND_HISTORY,
    roles: Optional[List[dict]] = None,
    members: Optional[List[dict]] = None,
    overwrites: Optional[List[dict]] = None,
    member_count: Optional[int] = None,
    threads: Optional[List[dict]] = None,
) -> discord.Guild:
    state = ConnectionState(
        dispatch=lambda *args: None, handlers={}, hooks={}, http=MagicMock(), intents=discord.Intents.all(),
        member_cache_flags=discord.MemberCacheFlags.all(), chunk_guilds_at_startup=False,
    )
    members = members if members is not None else [_member(5), _member(6)]
    data: dict = {
        "id": GUILD_ID, "name": "g", "owner_id": 99, "emojis": [], "features": [],
        "roles": [_role(GUILD_ID, everyone, 0)] + (roles or []),
        "channels": [{"id": 10, "type": 0, "name": "c", "position": 0, "permission_overwrites": overwrites or []}],
        "members": members, "member_count": member_count if member_count is not None else len(members),
        "threads": threads or [],
    }
    return discord.Guild(data=data, state=state)


def _private_thread(guild: discord.Guild, owner: int, members: List[int]) -> discord.Thread:
    thread = discord.Thread(
        guild=guild, state=guild._state,
        data={
            "id": 20, "guild_id": GUILD_ID, "parent_id": 10, "owner_id": owner, "name": "t", "type": 12,
            "message_count": 0, "member_count": len(members), "rate_limit_per_user": 0,
            "thread_metadata": {"archived": False, "auto_archive_duration": 60, "archive_timestamp": "2020-01-01T00:00:00+00:00", "locked": False},
        },
    )
    for user_id in members:
        thread._add_member(ThreadMember(parent=thread, data={"id": 20, "user_id": user_id, "join_timestamp": "2020-01-01T00:00:00+00:00", "flags": 0}))
    return thread


def test_a_role_deny_on_history_makes_the_audience_unable_to_read() -> None:
    guild = _guild(
        roles=[_role(2, discord.Permissions.none(), 1)],
        members=[_member(5, [2]), _member(6)],
        overwrites=[_overwrite(2, 0, deny=HISTORY)],
    )
    channel = guild.get_channel(10)

    assert can_read(channel, guild.get_member(6)) is True
    assert can_read(channel, guild.get_member(5)) is False
    assert audience_can_read(channel) is False


def test_a_role_restricted_channel_where_every_viewer_reads_the_history() -> None:
    guild = _guild(
        roles=[_role(2, discord.Permissions.none(), 1)],
        members=[_member(5, [2]), _member(6)],
        overwrites=[_overwrite(GUILD_ID, 0, deny=VIEW), _overwrite(2, 0, allow=VIEW_AND_HISTORY)],
    )
    channel = guild.get_channel(10)

    assert can_read(channel, guild.get_member(6)) is False
    assert audience_can_read(channel) is True


def test_a_member_overwrite_is_checked_on_its_own() -> None:
    guild = _guild(members=[_member(5), _member(6)], overwrites=[_overwrite(6, 1, deny=HISTORY)])

    assert audience_can_read(guild.get_channel(10)) is False


def test_an_incomplete_member_list_fails_closed() -> None:
    guild = _guild(members=[_member(5)], member_count=50)

    assert guild.chunked is False
    assert audience_can_read(guild.get_channel(10)) is False


def test_private_threads_count_only_their_current_members() -> None:
    guild = _guild(members=[_member(2), _member(3)])
    thread = _private_thread(guild, owner=2, members=[3])  # the creator has left

    assert can_read(thread, guild.get_member(3)) is True
    assert can_read(thread, guild.get_member(2)) is False
    assert audience_can_read(thread) is True


def test_a_thread_without_its_parent_fails_closed() -> None:
    guild = _guild(members=[_member(2)])
    thread = _private_thread(guild, owner=2, members=[2])
    guild._channels.pop(10)

    assert can_read(thread, guild.get_member(2)) is False
    assert audience_can_read(thread) is False
