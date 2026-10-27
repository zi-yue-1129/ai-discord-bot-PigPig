"""Date rules for community features: guild local time, birthdays and join anniversaries."""

from __future__ import annotations

import calendar
from datetime import date, datetime, timezone, tzinfo
from typing import Iterable, List, Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def parse_timezone(name: Optional[str]) -> Optional[tzinfo]:
    """Returns the time zone called ``name``, or None when it is empty or unknown."""
    if not name:
        return None
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return None


def local_now(now: datetime, guild_timezone: Optional[str], default_timezone: Optional[str] = None) -> datetime:
    """Converts an aware ``now`` to a guild's local time.

    The guild's own time zone wins, then the bot owner's default, then the host's local time.
    """
    zone = parse_timezone(guild_timezone) or parse_timezone(default_timezone)
    return now.astimezone(zone) if zone else now.astimezone()


def celebrated_on(month: int, day: int, year: int) -> Tuple[int, int]:
    """Returns the date a yearly ``month``/``day`` is celebrated in ``year`` (Feb 29 moves to Feb 28)."""
    if month == 2 and day == 29 and not calendar.isleap(year):
        return 2, 28
    return month, day


def is_valid_birthday(month: int, day: int) -> bool:
    """Returns whether ``month``/``day`` exists in some year (Feb 29 counts)."""
    if not 1 <= month <= 12:
        return False
    return 1 <= day <= calendar.monthrange(2024, month)[1]


def birthdays_on(today: date, birthdays: Iterable[Tuple[int, int, int]]) -> List[int]:
    """Returns the user IDs whose birthday is celebrated on ``today``.

    Args:
        today: The guild's local date.
        birthdays: ``(user_id, month, day)`` rows.
    """
    return [user_id for user_id, month, day in birthdays if celebrated_on(month, day, today.year) == (today.month, today.day)]


def anniversary_years(today: date, joined_at: Optional[datetime], local_zone: Optional[tzinfo]) -> int:
    """Returns how many full years a member has been in the guild if ``today`` is their join anniversary, else 0.

    Args:
        today: The guild's local date.
        joined_at: When the member joined (aware, as Discord gives it); None when unknown.
        local_zone: The guild's time zone, to tell which local day they joined on.
    """
    if joined_at is None:
        return 0
    if joined_at.tzinfo is None:
        joined_at = joined_at.replace(tzinfo=timezone.utc)
    joined = joined_at.astimezone(local_zone) if local_zone else joined_at.astimezone()
    years = today.year - joined.year
    if years < 1:
        return 0
    return years if celebrated_on(joined.month, joined.day, today.year) == (today.month, today.day) else 0


def upcoming_birthdays(
    today: date, birthdays: Iterable[Tuple[int, int, int]], within_days: int
) -> List[Tuple[int, date]]:
    """Returns ``(user_id, next date)`` for birthdays in the next ``within_days`` days (today included), soonest first."""
    found: List[Tuple[int, date]] = []
    for user_id, month, day in birthdays:
        for year in (today.year, today.year + 1):
            celebrated = date(year, *celebrated_on(month, day, year))
            if celebrated >= today:
                if (celebrated - today).days < within_days:
                    found.append((user_id, celebrated))
                break
    return sorted(found, key=lambda item: item[1])
