"""Achievement definitions and the rules for unlocking them from a member's message stats.

Each achievement lists minimum values for a few fixed stats; all of them must be reached.
The bot owner can replace the built-in list in the ``community.achievements`` block of
base.yaml. Built-in names and descriptions are translated; owner-defined ones are shown
as written.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional

from addons.logging import get_logger

logger = get_logger(server_id="Bot", source=__name__)

# Stats an achievement may require (minimum values).
VARIABLES = {
    "total_messages": "messages sent in the server",
    "streak_days": "consecutive days with a message",
    "gap_days": "days of silence before this message",
    "night_ratio": "share of messages sent between 0:00 and 4:59 (0-1)",
    "membership_days": "days since the first message in the server",
}
NIGHT_HOURS = range(0, 5)


@dataclass(frozen=True)
class Achievement:
    """One achievement.

    Attributes:
        id: Stable identifier (stored for every member who unlocked it).
        emoji: Shown before the name.
        when: Minimum value per stat in ``VARIABLES``; every one must be reached.
        name: Display name; None uses the translated built-in name.
        description: How to get it; None uses the translated built-in description.
    """

    id: str
    emoji: str
    when: Mapping[str, float] = field(default_factory=dict)
    name: Optional[str] = None
    description: Optional[str] = None


DEFAULT_ACHIEVEMENTS: List[Achievement] = [
    Achievement("msg_100", "💬", {"total_messages": 100}),
    Achievement("msg_1000", "📜", {"total_messages": 1000}),
    Achievement("msg_10000", "📚", {"total_messages": 10000}),
    Achievement("streak_7", "📅", {"streak_days": 7}),
    Achievement("streak_30", "🏅", {"streak_days": 30}),
    Achievement("night_owl", "🦉", {"night_ratio": 0.4, "total_messages": 200}),
    Achievement("diver", "🤿", {"gap_days": 30}),
    Achievement("revived", "🧟", {"gap_days": 180}),
    Achievement("veteran", "📼", {"membership_days": 365}),
]


def load_achievements(config: Optional[Iterable[Mapping[str, Any]]]) -> List[Achievement]:
    """Builds the achievement list from base.yaml; the built-in list when none is configured.

    Entries without an id or with an unknown or non-numeric stat are skipped (and logged).
    """
    if not config:
        return list(DEFAULT_ACHIEVEMENTS)
    loaded: List[Achievement] = []
    seen = set()
    for entry in config:
        if not isinstance(entry, Mapping) or not entry.get("id") or str(entry["id"]) in seen:
            logger.warning(f"Skipping an achievement without a unique id: {entry!r}")
            continue
        when_raw = entry.get("when") or {}
        try:
            when = {str(key): float(value) for key, value in dict(when_raw).items()}
        except (TypeError, ValueError):
            logger.warning(f"Skipping achievement {entry['id']}: its 'when' values must be numbers")
            continue
        unknown = set(when) - set(VARIABLES)
        if unknown or not when:
            logger.warning(f"Skipping achievement {entry['id']}: unknown or missing stats {sorted(unknown)}")
            continue
        seen.add(str(entry["id"]))
        loaded.append(
            Achievement(
                id=str(entry["id"]),
                emoji=str(entry.get("emoji") or "🏆"),
                when=when,
                name=str(entry["name"]) if entry.get("name") else None,
                description=str(entry["description"]) if entry.get("description") else None,
            )
        )
    return loaded


def _parse_time(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def stat_values(stats: Mapping[str, Any], now: datetime) -> Dict[str, float]:
    """Computes the ``VARIABLES`` for one member from their updated user_stats row.

    Args:
        stats: The row returned by ``StatsStorage.upsert_user_stats`` (with ``previous_active_at``).
        now: The current (aware) time.
    """
    total = float(stats.get("total_messages") or 0)
    hours = stats.get("active_hours") or {}
    night = sum(int(hours.get(str(hour), 0) or 0) for hour in NIGHT_HOURS)
    previous = _parse_time(stats.get("previous_active_at"))
    first = _parse_time(stats.get("first_message_at"))
    return {
        "total_messages": total,
        "streak_days": float(stats.get("streak_days") or 0),
        "gap_days": (now - previous).total_seconds() / 86400 if previous else 0.0,
        "night_ratio": night / total if total else 0.0,
        "membership_days": (now - first).total_seconds() / 86400 if first else 0.0,
    }


def reached(achievements: Iterable[Achievement], values: Mapping[str, float]) -> List[str]:
    """Returns the IDs of the achievements whose every requirement is met by ``values``."""
    return [a.id for a in achievements if all(values.get(key, 0.0) >= minimum for key, minimum in a.when.items())]
