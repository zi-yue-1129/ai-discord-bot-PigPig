"""When an episodic memory fragment happened and where it came from, as Discord renders them.

Times are given as Discord timestamps (``<t:UNIX:STYLE>``), which Discord shows in the viewer's own time
zone and language. The bot's prompt tells it to write every date and time that way; a date written out as
text (such as a UTC time) is copied into replies instead, so no text date is ever produced here.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Tuple

_UNKNOWN = "unknown"
_SECONDS_PER_MINUTE = 60
_SECONDS_PER_DAY = 86_400


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


def describe_fragment_time(metadata: Mapping[str, Any]) -> str:
    """Describe when a fragment happened as Discord timestamps, with the relative time.

    Args:
        metadata: The fragment's metadata.

    Returns:
        For example ``<t:1766795064:F> - <t:1766799202:t> (<t:1766795064:R>)``: the start, the end
        (as a clock time when it is within a day of the start, in full otherwise, left out when it
        is the same minute) and the relative time Discord keeps current ("308 days ago"). ``unknown``
        when the fragment has no usable time; nothing is guessed.
    """
    span = fragment_time_range(metadata)
    if span is None:
        return _UNKNOWN
    start, end = int(span[0]), int(span[1])
    if end - start < _SECONDS_PER_MINUTE:
        window = f"<t:{start}:F>"
    elif end - start < _SECONDS_PER_DAY:
        window = f"<t:{start}:F> - <t:{end}:t>"
    else:
        window = f"<t:{start}:F> - <t:{end}:F>"
    return f"{window} (<t:{start}:R>)"


def source_label(metadata: Mapping[str, Any]) -> str:
    """The label the bot copies when it uses a fragment: a link to the conversation and its relative time.

    Args:
        metadata: The fragment's metadata.

    Returns:
        For example ``[[Source <t:1766795064:R>](https://discord.com/channels/1/2/3)]``; without a
        usable time ``[[Source](url)]``; without a link ``[<t:1766795064:R>]``; empty with neither.
    """
    span = fragment_time_range(metadata)
    jump_url = metadata.get("jump_url")
    if jump_url and span is not None:
        return f"[[Source <t:{int(span[0])}:R>]({jump_url})]"
    if jump_url:
        return f"[[Source]({jump_url})]"
    if span is not None:
        return f"[<t:{int(span[0])}:R>]"
    return ""
