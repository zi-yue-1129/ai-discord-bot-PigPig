"""The bot owner's limits for community features, read from the ``community:`` block of base.yaml."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from addons.logging import get_logger

logger = get_logger(server_id="Bot", source=__name__)


def _number(
    raw: Mapping[str, Any], key: str, default: float, minimum: float = 0, maximum: float = math.inf
) -> float:
    """Reads a number, falling back to ``default`` when it is missing or invalid (not a number,
    true/false, a quoted string, infinite or NaN); values above ``maximum`` are capped to it."""
    raw_value = raw.get(key, default)
    if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
        logger.warning(f"community limit {key!r} is not a number ({raw_value!r}), using {default}")
        return default
    try:
        value = float(raw_value)
    except OverflowError:
        value = math.inf
    if not math.isfinite(value) or value < minimum:
        logger.warning(f"community limit {key!r} is out of range ({raw_value!r}), using {default}")
        return default
    if value > maximum:
        logger.warning(f"community limit {key!r} is above {maximum} ({raw_value!r}), using {maximum}")
        return maximum
    return value


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
        playing_min_minutes: How long each member must have been playing the game.
        playing_cooldown_hours: Hours before the same game is pointed out again in a server.
        playing_max_per_day: Posts per server in 24 hours (0 turns the feature off).
        playing_use_ai: Whether the post is written by the model.
        playing_max_mentions: Most people named in one post.
        playing_max_rooms: Voice rooms the bot keeps open per server at once (0: no button).
        playing_room_idle_minutes: A room nobody joined is deleted after this long.
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
    playing_min_minutes: float = 10
    playing_cooldown_hours: float = 3
    playing_max_per_day: int = 5
    playing_use_ai: bool = True
    playing_max_mentions: int = 10
    playing_max_rooms: int = 3
    playing_room_idle_minutes: float = 5

    @classmethod
    def from_config(cls, config: Optional[Mapping[str, Any]]) -> "CommunityLimits":
        config = config or {}
        welcome = config.get("welcome") or {}
        birthday = config.get("birthday") or {}
        weekly = config.get("weekly") or {}
        playing = config.get("playing") or {}
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
            playing_min_minutes=_number(playing, "min_minutes", defaults.playing_min_minutes),
            playing_cooldown_hours=_number(playing, "cooldown_hours", defaults.playing_cooldown_hours, maximum=30 * 24),
            playing_max_per_day=int(_number(playing, "max_per_day", defaults.playing_max_per_day)),
            playing_use_ai=bool(playing.get("use_ai", defaults.playing_use_ai)),
            playing_max_mentions=int(_number(playing, "max_mentions", defaults.playing_max_mentions, 2)),
            playing_max_rooms=int(_number(playing, "max_rooms", defaults.playing_max_rooms)),
            playing_room_idle_minutes=_number(playing, "room_idle_minutes", defaults.playing_room_idle_minutes, 1),
        )
