"""Who can read a channel: one rule for every feature that repeats channel content elsewhere.

``can_read(channel, member)`` is whether one member may see the channel and read its message
history. ``audience_can_read(channel)`` is whether *everyone* who can see the channel can also
read its history, i.e. whether a post there may retell older messages.

A private thread inherits its permissions from the parent channel, but only the people in it
(and moderators who can manage threads) can open it, so its member list counts too.

Both fail closed: whatever cannot be established (a thread whose parent is not cached, a
thread's members not known) counts as not readable.
"""

from __future__ import annotations

from typing import Any

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


_READ = ("view_channel", "read_message_history")


def audience_can_read(channel: Any) -> bool:
    """Whether everyone who can see ``channel`` can also read its history.

    Decided from the channel's own permissions, never from a member list: ``@everyone`` must be
    able to see the channel and read its history, and no role or member overwrite on it (for a
    thread: on its parent) may deny either. Private threads and threads whose parent is unknown
    are never readable by their whole audience. This errs only towards "not shown": a channel
    restricted to a role that can read everything counts as not readable too.
    """
    if channel is None or _is_private_thread(channel):
        return False
    base = getattr(channel, "parent", None) if _is_thread(channel) else channel
    guild = getattr(base, "guild", None)
    if base is None or guild is None or getattr(guild, "default_role", None) is None:
        return False
    everyone = _permissions(base, guild.default_role)
    if everyone is None or not all(getattr(everyone, name, False) for name in _READ):
        return False
    overwrites = getattr(base, "overwrites", None)
    if overwrites is None:
        return False
    for overwrite in overwrites.values():
        _, deny = overwrite.pair()
        if any(getattr(deny, name, False) for name in _READ):
            return False
    return True
