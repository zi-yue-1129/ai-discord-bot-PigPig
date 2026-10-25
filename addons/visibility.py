"""Who can read a channel: one rule for every feature that repeats channel content elsewhere.

``can_read(channel, member)`` is whether one member may see the channel and read its message
history. ``audience_can_read(channel)`` is whether *everyone* who can see the channel can also
read its history, i.e. whether a post there may retell older messages.

A private thread inherits its permissions from the parent channel, but only the people in it
(and moderators who can manage threads) can open it, so its member list counts too.

Both fail closed: whatever cannot be established (a thread whose parent is not cached, a
member list that is not complete, a thread's members not known) counts as not readable.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import discord


def _permissions(channel: Any, member: Any) -> Any:
    try:
        return channel.permissions_for(member)
    except (AttributeError, TypeError, discord.ClientException):
        return None


def _is_thread(channel: Any) -> bool:
    return getattr(channel, "type", None) in (discord.ChannelType.private_thread, discord.ChannelType.public_thread, discord.ChannelType.news_thread)


def _is_private_thread(channel: Any) -> bool:
    return getattr(channel, "type", None) == discord.ChannelType.private_thread


def _thread_member_ids(thread: Any) -> set:
    """The people in a thread, as far as they are known (the creator only while still in it)."""
    return {getattr(member, "id", None) for member in getattr(thread, "members", None) or []}


def can_read(channel: Any, member: Any) -> bool:
    """Whether ``member`` may see ``channel`` and read its message history."""
    if channel is None or member is None:
        return False
    permissions = _permissions(channel, member)
    if permissions is None or not (permissions.view_channel and permissions.read_message_history):
        return False
    if _is_private_thread(channel):
        return getattr(member, "id", None) in _thread_member_ids(channel) or bool(permissions.manage_threads)
    return True


def _overwritten_member_ids(channel: Any) -> set:
    """Members with an overwrite of their own on ``channel`` (their permissions are not their roles')."""
    overwrites = getattr(channel, "overwrites", None) or {}
    return {getattr(target, "id", None) for target in overwrites if not isinstance(target, discord.Role)}


def audience_can_read(channel: Any) -> bool:
    """Whether everyone who can see ``channel`` can also read its history.

    Needs the guild's complete member list (``guild.chunked``). Members are grouped by their
    roles, so permissions are worked out once per role combination; members with an overwrite of
    their own, the owner, and members of a private thread are checked one by one.
    """
    guild = getattr(channel, "guild", None)
    if guild is None or getattr(guild, "chunked", False) is not True:
        return False
    base = channel
    if _is_thread(channel):
        base = getattr(channel, "parent", None)
        if base is None:
            return False
    individual = _overwritten_member_ids(base) | {getattr(guild, "owner_id", None)}
    private = _is_private_thread(channel)
    in_thread = _thread_member_ids(channel) if private else set()
    cache: Dict[Tuple, Any] = {}
    for member in getattr(guild, "members", None) or []:
        key: Tuple = (member.id,) if member.id in individual else tuple(sorted(role.id for role in member.roles))
        permissions: Optional[Any] = cache.get(key)
        if permissions is None:
            permissions = _permissions(channel, member)
            if permissions is None:
                return False
            cache[key] = permissions
        sees = permissions.view_channel and (not private or member.id in in_thread or permissions.manage_threads)
        if sees and not permissions.read_message_history:
            return False
    return True
