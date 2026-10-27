"""Keeps what hidden members (``/leaderboard optout``) said out of the bot's long-term memory replies.

A memory fragment is a summary of a conversation; its metadata names the people in it. A fragment
with a hidden member in it is neither injected into a reply's context nor returned by the search
tool, whoever asks: the summary would retell what the member said. When it cannot be read who is
hidden, no fragment is used at all.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, Iterable, List, Mapping, Optional, Set


def fragment_user_ids(metadata: Optional[Mapping[str, Any]]) -> Set[int]:
    """The Discord ids a fragment's metadata names as taking part (``author_ids``, which the memory
    ingestion writes, ``user_ids`` or ``author_id``).

    Entries that are not numbers are ignored.
    """
    found: Set[int] = set()
    meta = metadata or {}
    values: List[Any] = []
    for key in ("author_ids", "user_ids", "author_id"):
        field = meta.get(key)
        if isinstance(field, (list, tuple, set, frozenset)):
            values.extend(field)
        elif field is not None:  # a single id: a string must not be split into its characters
            values.append(field)
    for value in values:
        try:
            found.add(int(value))
        except (TypeError, ValueError):
            continue
    return found


def without_hidden_participants(fragments: Iterable[Any], hidden: Optional[Set[int]]) -> List[Any]:
    """The fragments none of whose participants is hidden; none at all when ``hidden`` is None
    (the opt-out list could not be read)."""
    if hidden is None:
        return []
    return [fragment for fragment in fragments if not (fragment_user_ids(getattr(fragment, "metadata", None)) & hidden)]


def is_hidden_id(user_id: Any, hidden: Set[int]) -> bool:
    """Whether ``user_id`` (a number or a numeric string) is one of the ``hidden`` members."""
    try:
        return int(user_id) in hidden
    except (TypeError, ValueError):
        return False


def hidden_in_guild(bot: Any, guild_id: int) -> Optional[Set[int]]:
    """The members of ``guild_id`` who hid themselves; None when the opt-out list cannot be read."""
    from llm.tools.user_stats import hidden_member_ids

    return hidden_member_ids(SimpleNamespace(bot=bot), guild_id)


async def hidden_in_guild_async(bot: Any, guild_id: int) -> Optional[Set[int]]:
    """``hidden_in_guild`` read on a worker thread, so a locked database cannot stall the event loop."""
    return await asyncio.to_thread(hidden_in_guild, bot, guild_id)
