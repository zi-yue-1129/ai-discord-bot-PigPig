"""Tracks member joins per guild: batching close joins, spotting raids, and budgeting AI welcomes."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Deque, Dict, List

AI_WINDOW_SECONDS = 3600


class JoinTracker:
    """Decides how each batch of new members is welcomed.

    Joins that arrive within ``batch_seconds`` of the first one share one welcome. When
    ``burst_threshold`` joins land within ``burst_seconds`` the guild is treated as raided
    and only the fixed text is used, which also keeps a raid from burning model calls.
    AI welcomes are capped at ``max_ai_per_hour`` per guild.
    """

    def __init__(self, burst_threshold: int, burst_seconds: float, max_ai_per_hour: int) -> None:
        self.burst_threshold = burst_threshold
        self.burst_seconds = burst_seconds
        self.max_ai_per_hour = max_ai_per_hour
        self._joins: Dict[int, Deque[float]] = defaultdict(deque)
        self._ai_uses: Dict[int, Deque[float]] = defaultdict(deque)
        self._pending: Dict[int, List[Any]] = {}

    def add(self, guild_id: int, member: Any, now: float) -> bool:
        """Records a join; returns True when it starts a new batch (the caller then schedules a flush)."""
        joins = self._joins[guild_id]
        joins.append(now)
        while joins and now - joins[0] > self.burst_seconds:
            joins.popleft()
        batch = self._pending.get(guild_id)
        if batch is None:
            self._pending[guild_id] = [member]
            return True
        batch.append(member)
        return False

    def take_batch(self, guild_id: int) -> List[Any]:
        """Returns and clears the members waiting to be welcomed."""
        return self._pending.pop(guild_id, [])

    def is_raid(self, guild_id: int, now: float) -> bool:
        """Returns whether the guild had a burst of joins in the last ``burst_seconds``."""
        joins = self._joins[guild_id]
        return sum(1 for moment in joins if now - moment <= self.burst_seconds) >= self.burst_threshold

    def use_ai(self, guild_id: int, now: float) -> bool:
        """Spends one AI welcome from the guild's hourly budget; False when it is used up."""
        uses = self._ai_uses[guild_id]
        while uses and now - uses[0] > AI_WINDOW_SECONDS:
            uses.popleft()
        if len(uses) >= self.max_ai_per_hour:
            return False
        uses.append(now)
        return True
