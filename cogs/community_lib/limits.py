"""The bot owner's limits for community features, read from the ``community:`` block of base.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


def _number(raw: Mapping[str, Any], key: str, default: float, minimum: float = 0) -> float:
    """Reads a number, falling back to ``default`` when it is missing or invalid."""
    try:
        value = float(raw.get(key, default))
    except (TypeError, ValueError):
        return default
    return value if value >= minimum else default


@dataclass(frozen=True)
class CommunityLimits:
    """Owner-set limits; missing or invalid values fall back to the defaults below.

    Attributes:
        default_timezone: Time zone for servers that set none; empty uses the host's.
        welcome_max_ai_per_hour: AI-written welcomes per server per hour (0: never use AI).
        welcome_burst_threshold: Joins within ``welcome_burst_seconds`` that count as a raid.
        welcome_burst_seconds: The raid window.
        welcome_batch_seconds: Joins this close together share one welcome.
        birthday_use_ai: Whether birthday and anniversary messages are AI-written.
        birthday_max_mentions: Most people named in one celebration message.
        weekly_min_messages: Weeks with fewer messages get no recap.
        weekly_use_ai: Whether the recap gets an AI-written news paragraph.
        weekly_max_report_chars: Length asked of the AI paragraph.
        missing_after_days: Silence after which a former regular is listed as missing.
        missing_min_messages: Messages someone needs to count as a former regular.
        missing_max: Most people listed as missing in one recap.
    """

    default_timezone: str = ""
    welcome_max_ai_per_hour: int = 20
    welcome_burst_threshold: int = 5
    welcome_burst_seconds: float = 60
    welcome_batch_seconds: float = 5
    birthday_use_ai: bool = True
    birthday_max_mentions: int = 20
    weekly_min_messages: int = 50
    weekly_use_ai: bool = True
    weekly_max_report_chars: int = 300
    missing_after_days: int = 30
    missing_min_messages: int = 50
    missing_max: int = 3

    @classmethod
    def from_config(cls, config: Optional[Mapping[str, Any]]) -> "CommunityLimits":
        config = config or {}
        welcome = config.get("welcome") or {}
        birthday = config.get("birthday") or {}
        weekly = config.get("weekly") or {}
        defaults = cls()
        return cls(
            default_timezone=str(config.get("default_timezone") or ""),
            welcome_max_ai_per_hour=int(_number(welcome, "max_ai_per_hour", defaults.welcome_max_ai_per_hour)),
            welcome_burst_threshold=int(_number(welcome, "burst_threshold", defaults.welcome_burst_threshold, 2)),
            welcome_burst_seconds=_number(welcome, "burst_seconds", defaults.welcome_burst_seconds, 1),
            welcome_batch_seconds=_number(welcome, "batch_seconds", defaults.welcome_batch_seconds),
            birthday_use_ai=bool(birthday.get("use_ai", defaults.birthday_use_ai)),
            birthday_max_mentions=int(_number(birthday, "max_mentions", defaults.birthday_max_mentions, 1)),
            weekly_min_messages=int(_number(weekly, "min_messages", defaults.weekly_min_messages)),
            weekly_use_ai=bool(weekly.get("use_ai", defaults.weekly_use_ai)),
            weekly_max_report_chars=int(_number(weekly, "max_report_chars", defaults.weekly_max_report_chars, 50)),
            missing_after_days=int(_number(weekly, "missing_after_days", defaults.missing_after_days, 1)),
            missing_min_messages=int(_number(weekly, "missing_min_messages", defaults.missing_min_messages)),
            missing_max=int(_number(weekly, "missing_max", defaults.missing_max)),
        )
