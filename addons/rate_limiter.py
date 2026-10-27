"""Per-user usage limits for AI chat and image generation.

The bot owner sets the limits in ``base.yaml`` under ``rate_limits``. Each
limit allows ``max_requests`` uses in a sliding window of ``per_seconds``
seconds; a ``max_requests`` of 0 turns that limit off.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable, Deque, Dict, Iterable, Mapping, Optional, Tuple

# Used when base.yaml has no ``rate_limits`` block, or leaves a bucket out.
DEFAULT_LIMITS: Dict[str, Dict[str, float]] = {
    "chat": {"max_requests": 10, "per_seconds": 60},
    "image": {"max_requests": 20, "per_seconds": 86400},
    # Questions the AI posts to another member on someone's behalf (a reminder or a memory for them);
    # each pings that member.
    "ask_others": {"max_requests": 3, "per_seconds": 3600},
}


@dataclass(frozen=True)
class LimitRule:
    """``max_requests`` uses per ``per_seconds``; ``max_requests <= 0`` means unlimited."""

    max_requests: int
    per_seconds: float

    @property
    def unlimited(self) -> bool:
        return self.max_requests <= 0 or self.per_seconds <= 0


class RateLimiter:
    """Sliding-window limiter keyed by (bucket, user id)."""

    def __init__(
        self,
        rules: Mapping[str, LimitRule],
        exempt_user_ids: Iterable[int] = (),
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.rules = dict(rules)
        self.exempt_user_ids = {int(u) for u in exempt_user_ids if u}
        self._clock = clock
        self._hits: Dict[Tuple[str, int], Deque[float]] = defaultdict(deque)
        self._notified_until: Dict[Tuple[str, int], float] = {}

    @classmethod
    def from_config(cls, config: Mapping | None, owner_id: int = 0, **kwargs) -> "RateLimiter":
        config = config or {}
        rules: Dict[str, LimitRule] = {}
        for bucket, default in DEFAULT_LIMITS.items():
            raw = config.get(bucket) or {}
            rules[bucket] = LimitRule(
                max_requests=int(raw.get("max_requests", default["max_requests"])),
                per_seconds=float(raw.get("per_seconds", default["per_seconds"])),
            )
        exempt = [owner_id] if config.get("exempt_owner", True) else []
        return cls(rules, exempt_user_ids=exempt, **kwargs)

    def hit(self, bucket: str, user_id: int) -> float:
        """Record one use and return 0, or return the seconds to wait when over the limit."""
        return self.take(bucket, user_id)[0]

    def take(self, bucket: str, user_id: int) -> Tuple[float, Optional["Use"]]:
        """Like :meth:`hit`, and also returns the recorded use (None when nothing was recorded),
        which :meth:`refund` can give back."""
        rule = self.rules.get(bucket)
        if rule is None or rule.unlimited or int(user_id) in self.exempt_user_ids:
            return 0.0, None

        now = self._clock()
        window = self._hits[(bucket, int(user_id))]
        while window and now - window[0] >= rule.per_seconds:
            window.popleft()

        if len(window) >= rule.max_requests:
            return max(rule.per_seconds - (now - window[0]), 0.1), None

        window.append(now)
        return 0.0, Use(bucket, int(user_id), now)

    def refund(self, use: Optional["Use"]) -> None:
        """Gives back a use from :meth:`take` (for a request that produced nothing); only once."""
        if use is None or use.refunded:
            return
        use.refunded = True
        window = self._hits.get((use.bucket, use.user_id))
        if window is not None and use.at in window:
            window.remove(use.at)

    def should_notify(self, bucket: str, user_id: int, retry_after: float) -> bool:
        """True the first time a user is blocked in a window, so the bot says so only once."""
        key = (bucket, int(user_id))
        now = self._clock()
        if self._notified_until.get(key, 0.0) > now:
            return False
        self._notified_until[key] = now + retry_after
        return True


@dataclass
class Use:
    """One recorded use of a bucket."""

    bucket: str
    user_id: int
    at: float
    refunded: bool = False


def format_wait(seconds: float) -> int:
    """Whole seconds to show the user, never 0."""
    return max(int(seconds + 0.999), 1)
