"""When an episodic memory fragment happened, read from the fields the vector store really keeps."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Tuple

_SECONDS_PER_DAY = 86_400
_UNKNOWN = "unknown"


def _usable_timestamp(value: Any) -> Optional[float]:
    """Return ``value`` as UNIX seconds, or None when it is not a plausible time.

    Args:
        value: A stored metadata value.

    Returns:
        The seconds as a float, or None for missing, non-numeric, non-finite, negative values or
        values no date can hold (past the year 9999).
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    seconds = float(value)
    if not math.isfinite(seconds) or seconds < 0:
        return None
    try:
        datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None
    return seconds


def fragment_time_range(metadata: Mapping[str, Any]) -> Optional[Tuple[float, float]]:
    """Return the start and end of the conversation a fragment summarizes.

    Fragments store ``start_timestamp`` and ``end_timestamp``; the older single ``timestamp`` key
    is read as both ends, like the automatic recall does.

    Args:
        metadata: The fragment's metadata.

    Returns:
        ``(start, end)`` in UNIX seconds with ``start <= end``, or None when no usable start exists.
    """
    start = _usable_timestamp(metadata.get("start_timestamp"))
    if start is None:
        start = _usable_timestamp(metadata.get("timestamp"))
    if start is None:
        return None
    end = _usable_timestamp(metadata.get("end_timestamp"))
    if end is None or end < start:
        end = start
    return start, end


def describe_fragment_time(metadata: Mapping[str, Any], now: Optional[datetime] = None) -> str:
    """Describe when a fragment happened, in UTC, with how long ago that was.

    Args:
        metadata: The fragment's metadata.
        now: The current time, for tests; defaults to the present moment.

    Returns:
        For example ``2025-12-27 00:24 - 01:33 UTC (308 days ago)``, or ``unknown`` when the
        fragment has no usable time (nothing is guessed).
    """
    span = fragment_time_range(metadata)
    if span is None:
        return _UNKNOWN
    start = datetime.fromtimestamp(span[0], tz=timezone.utc)
    end = datetime.fromtimestamp(span[1], tz=timezone.utc)
    current = now or datetime.now(timezone.utc)

    if start.replace(second=0, microsecond=0) == end.replace(second=0, microsecond=0):
        window = f"{start:%Y-%m-%d %H:%M}"
    elif start.date() == end.date():
        window = f"{start:%Y-%m-%d %H:%M} - {end:%H:%M}"
    else:
        window = f"{start:%Y-%m-%d %H:%M} - {end:%Y-%m-%d %H:%M}"

    days_ago = (current - start).days
    if days_ago < 1:
        age = "today" if current.date() == start.date() else "yesterday"
    elif days_ago == 1:
        age = "1 day ago"
    else:
        age = f"{days_ago} days ago"
    return f"{window} UTC ({age})"
