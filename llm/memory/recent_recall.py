"""Episodic memories the bot recalled a moment ago, kept per channel so a follow-up can still use them.

The context of every message is built from scratch: the reply only sees the last Discord messages, so
what the search tool found for one message was gone at the next one, and a short follow-up such as
"when was that?" found nothing in the vector search either. This store keeps the recalled fragments
for a short time. It is only memory in the process: nothing is written to disk, a restart forgets it.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, FrozenSet, Iterable, List, Mapping, Set

from llm.memory.privacy import fragment_user_ids


@dataclass(frozen=True)
class RecalledFragment:
    """One remembered fragment.

    Attributes:
        key: The fragment id, or its content when it has none; the same fragment has the same key.
        content: The fragment's summary text.
        metadata: The fragment's metadata (time, jump link, participants).
        participants: Discord ids of the people in it, checked again each time it is read.
        expires_at: When it is forgotten, on the store's clock.
    """

    key: str
    content: str
    metadata: Mapping[str, Any]
    participants: FrozenSet[int]
    expires_at: float


class RecentRecall:
    """Per-channel store of recently recalled fragments with a time limit and size limits.

    Not thread-safe on purpose: every method is synchronous and has no await, so on the event loop
    one call cannot be interrupted by another.

    Args:
        ttl: Seconds a fragment is kept after it was last recalled.
        max_per_channel: Fragments kept per channel; the newest win.
        max_channels: Channels kept; the channels recalled longest ago are forgotten first.
        clock: Returns the current time in seconds; replaceable for tests.

    Raises:
        ValueError: If a limit is not positive.
    """

    def __init__(
        self,
        ttl: float = 600.0,
        max_per_channel: int = 5,
        max_channels: int = 200,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if ttl <= 0:
            raise ValueError("ttl must be > 0")
        if max_per_channel < 1:
            raise ValueError("max_per_channel must be >= 1")
        if max_channels < 1:
            raise ValueError("max_channels must be >= 1")
        self.ttl = ttl
        self.max_per_channel = max_per_channel
        self.max_channels = max_channels
        self._clock = clock
        # channel id -> (fragment key -> fragment), the most recently recalled last in both levels
        self._channels: "OrderedDict[str, OrderedDict[str, RecalledFragment]]" = OrderedDict()

    @staticmethod
    def _key(fragment: Any) -> str:
        """Identify a fragment by its id, or by its content when it has no id."""
        metadata = getattr(fragment, "metadata", None) or {}
        fragment_id = metadata.get("fragment_id") or getattr(fragment, "id", None)
        return str(fragment_id) if fragment_id else f"content:{getattr(fragment, 'content', '')}"

    def remember(self, channel_id: str, fragments: Iterable[Any]) -> None:
        """Keep ``fragments`` for ``channel_id``; one already kept is renewed and becomes the newest.

        Args:
            channel_id: The channel they were recalled in.
            fragments: Memory fragments with ``content`` and ``metadata``. The caller has already
                left out the ones of hidden members; they are checked again when read.
        """
        expires_at = self._clock() + self.ttl
        kept = self._channels.setdefault(channel_id, OrderedDict())
        for fragment in fragments:
            key = self._key(fragment)
            metadata = dict(getattr(fragment, "metadata", None) or {})
            kept.pop(key, None)
            kept[key] = RecalledFragment(
                key=key,
                content=str(getattr(fragment, "content", "")),
                metadata=metadata,
                participants=frozenset(fragment_user_ids(metadata)),
                expires_at=expires_at,
            )
        while len(kept) > self.max_per_channel:
            kept.popitem(last=False)
        self._channels.move_to_end(channel_id)
        while len(self._channels) > self.max_channels:
            self._channels.popitem(last=False)

    def recall(self, channel_id: str, hidden: Set[int]) -> List[RecalledFragment]:
        """The fragments still kept for ``channel_id``, newest first.

        Expired ones and those with a hidden participant are dropped for good.

        Args:
            channel_id: The channel to read.
            hidden: Discord ids of the members who hid themselves (``/leaderboard optout``).

        Returns:
            The usable fragments, newest first; empty for an unknown channel.
        """
        kept = self._channels.get(channel_id)
        if kept is None:
            return []
        now = self._clock()
        for key in [key for key, fragment in kept.items() if fragment.expires_at <= now or fragment.participants & hidden]:
            del kept[key]
        if not kept:
            del self._channels[channel_id]
            return []
        return list(reversed(kept.values()))
