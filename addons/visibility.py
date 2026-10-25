"""Who can read a channel: one rule for every feature that repeats channel content elsewhere.

``can_read(channel, member)`` is whether one member may see the channel and read its message
history. ``audience_can_read(channel)`` is whether *everyone* who can see the channel can also
read its history, i.e. whether a post there may retell older messages.

A private thread inherits its permissions from the parent channel, but only the people added to
it (and moderators who can manage threads) can open it, so its membership counts too. Anything
that cannot be resolved (a thread whose parent is not cached, members not cached) counts as
not readable: left out, never leaked.
"""

from __future__ import annotations

from typing import Any, Iterable

import discord


def _permissions(channel: Any, member: Any) -> Any:
    try:
        return channel.permissions_for(member)
    except (AttributeError, TypeError, discord.ClientException):
        return None


def _thread_member_ids(thread: Any) -> set:
    ids = {getattr(member, "id", None) for member in getattr(thread, "members", []) or []}
    owner = getattr(thread, "owner_id", None)
    if owner is not None:
        ids.add(owner)
    return ids


def can_read(channel: Any, member: Any) -> bool:
    """Whether ``member`` may see ``channel`` and read its message history."""
    if channel is None or member is None:
        return False
    permissions = _permissions(channel, member)
    if permissions is None or not (permissions.view_channel and permissions.read_message_history):
        return False
    if getattr(channel, "type", None) == discord.ChannelType.private_thread:
        return getattr(member, "id", None) in _thread_member_ids(channel) or bool(permissions.manage_threads)
    return True


def viewers(channel: Any, members: Iterable[Any]) -> list:
    """The members who can see ``channel`` (for a private thread: its members and moderators)."""
    found = []
    for member in members:
        permissions = _permissions(channel, member)
        if permissions is None or not permissions.view_channel:
            continue
        if getattr(channel, "type", None) == discord.ChannelType.private_thread:
            if member.id not in _thread_member_ids(channel) and not permissions.manage_threads:
                continue
        found.append(member)
    return found


def audience_can_read(channel: Any) -> bool:
    """Whether everyone who can see ``channel`` can also read its history.

    Checked member by member (roles, role overwrites and member overwrites all count), so a
    role that may see new messages but not the history makes this False.
    """
    guild = getattr(channel, "guild", None)
    members = getattr(guild, "members", None)
    if not members:
        return False
    return all(can_read(channel, member) for member in viewers(channel, members))
