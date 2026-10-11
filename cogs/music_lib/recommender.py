"""Autoplay recommendation: candidate filtering, ranking and a per-guild taste memory."""

from __future__ import annotations

import random
import re
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, Iterable, List, Optional, Set, Tuple

# Score weights, relative to a Mix order score that runs from 1.0 (first) down to 0.
REQUEST_BONUS_PER_REQUEST = 0.3
MAX_COUNTED_REQUESTS = 3
SKIP_PENALTY_PER_SKIP = 0.5
MAX_COUNTED_SKIPS = 2
SEED_AUTHOR_BONUS = 0.05

_DECORATION_SEPARATED = re.compile(r"\s*-\s*(topic|vevo|official)\b.*$", re.IGNORECASE)
_DECORATION_TRAILING = re.compile(r"\s+(topic|vevo|official)$", re.IGNORECASE)


def normalize_author(author: str) -> str:
    """Reduces a channel name to the artist so "X - Topic" and "X" compare equal.

    Args:
        author: The uploader / channel name.

    Returns:
        The lower-cased name without "Topic", "VEVO" or "Official" decorations.
    """
    name = _DECORATION_SEPARATED.sub("", author.strip())
    name = _DECORATION_TRAILING.sub("", name)
    return name.strip().lower()


@dataclass
class TasteMemory:
    """What one guild has played, requested and skipped.

    With a ``store`` the memory is loaded from it and every change is saved to it, so it
    survives restarts; without one it lives in memory only.

    Attributes:
        history_size: How many recently played video IDs are remembered.
        requested: Count of explicit user requests per normalized author.
        skipped: Count of quickly skipped recommendations per normalized author.
        store: Where the memory is persisted, if anywhere.
        guild_id: The guild this memory belongs to (key in the store).
    """

    history_size: int
    requested: Counter = field(default_factory=Counter)
    skipped: Counter = field(default_factory=Counter)
    store: Optional[Any] = None
    guild_id: int = 0
    _history: Deque[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._history = deque(maxlen=self.history_size)
        if self.store is not None:
            played, self.requested, self.skipped = self.store.load(self.guild_id, self.history_size)
            self._history.extend(played)

    def record_played(self, video_id: str) -> None:
        """Remembers that a song was played."""
        self._history.append(video_id)
        if self.store is not None:
            self.store.add_played(self.guild_id, video_id, self.history_size)

    def played_ids(self) -> Set[str]:
        """Returns the recently played video IDs."""
        return set(self._history)

    def record_request(self, author: str) -> None:
        """Counts a user's explicit request for a song by ``author``."""
        name = normalize_author(author)
        self.requested[name] += 1
        if self.store is not None:
            self.store.add_request(self.guild_id, name)

    def record_skip(self, author: str) -> None:
        """Counts a recommendation by ``author`` that was skipped right away."""
        name = normalize_author(author)
        self.skipped[name] += 1
        if self.store is not None:
            self.store.add_skip(self.guild_id, name)


def filter_candidates(
    candidates: Iterable[Dict[str, Any]],
    *,
    exclude_ids: Set[str],
    min_duration: int,
    max_duration: int,
    banned_keywords: Tuple[str, ...],
) -> List[Dict[str, Any]]:
    """Drops candidates that must not be recommended, keeping the original order.

    Args:
        candidates: Song-like dicts (``video_id``, ``title``, ``duration``, ``is_live``).
        exclude_ids: Video IDs already queued, playing or recently played.
        min_duration: Shortest acceptable length in seconds.
        max_duration: Longest acceptable length in seconds.
        banned_keywords: Title keywords (case-insensitive) that disqualify a song.

    Returns:
        The acceptable candidates.
    """
    banned = tuple(keyword.lower() for keyword in banned_keywords)
    kept = []
    for candidate in candidates:
        video_id = candidate.get("video_id")
        duration = candidate.get("duration") or 0
        title = str(candidate.get("title") or "").lower()
        if not video_id or video_id in exclude_ids or candidate.get("is_live"):
            continue
        if not min_duration <= duration <= max_duration:
            continue
        if any(keyword in title for keyword in banned):
            continue
        kept.append(candidate)
    return kept


def rank_candidates(
    candidates: List[Dict[str, Any]],
    *,
    seed_author: str,
    taste: TasteMemory,
    max_per_author: int,
    limit: int,
    rng: random.Random,
    jitter: float = 0.1,
) -> List[Dict[str, Any]]:
    """Picks the best ``limit`` candidates.

    The score starts from the Mix order, favors authors the guild requests, demotes authors
    whose recommendations get skipped, and adds a little seeded jitter. No author may supply
    more than ``max_per_author`` songs unless nothing else is left.

    Args:
        candidates: Filtered candidates in Mix order.
        seed_author: The author of the song the recommendations start from.
        taste: The guild's taste memory.
        max_per_author: Cap per author in one batch.
        limit: How many songs to return.
        rng: Random generator for the jitter (seeded by the caller).
        jitter: Maximum random score added to each candidate.

    Returns:
        Up to ``limit`` candidates, best first.
    """
    total = len(candidates)
    seed_name = normalize_author(seed_author)
    scored: List[Tuple[float, Dict[str, Any]]] = []
    for index, candidate in enumerate(candidates):
        name = normalize_author(str(candidate.get("author") or ""))
        score = 1.0 - index / total
        score += REQUEST_BONUS_PER_REQUEST * min(taste.requested[name], MAX_COUNTED_REQUESTS)
        score -= SKIP_PENALTY_PER_SKIP * min(taste.skipped[name], MAX_COUNTED_SKIPS)
        if name == seed_name:
            score += SEED_AUTHOR_BONUS
        score += rng.uniform(0.0, jitter)
        scored.append((score, candidate))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    chosen: List[Dict[str, Any]] = []
    leftovers: List[Dict[str, Any]] = []
    per_author: Counter = Counter()
    for _, candidate in scored:
        name = normalize_author(str(candidate.get("author") or ""))
        if len(chosen) < limit and per_author[name] < max_per_author:
            chosen.append(candidate)
            per_author[name] += 1
        else:
            leftovers.append(candidate)
    chosen.extend(leftovers[: limit - len(chosen)])
    return chosen
