"""What a member is playing, read from their Discord presence (needs the presences intent).

Only games count: a ``discord.Game`` or any activity of type ``playing``. Spotify, streams and
custom statuses are not games.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, Tuple

import discord


def is_game(activity: Any) -> bool:
    """Whether a presence activity is a game being played."""
    if isinstance(activity, discord.Game):
        return True
    if isinstance(activity, (discord.Spotify, discord.CustomActivity, discord.Streaming)):
        return False
    return getattr(activity, "type", None) == discord.ActivityType.playing and bool(getattr(activity, "name", None))


def current_game(member: Any) -> Optional[Tuple[str, Optional[datetime]]]:
    """The game ``member`` is playing as ``(name, started_at)``, or None.

    ``started_at`` is when Discord says the game started (timezone-aware), or None when it does
    not say. With several games, the first one Discord lists counts.
    """
    for activity in getattr(member, "activities", None) or ():
        if not is_game(activity):
            continue
        name = " ".join(str(getattr(activity, "name", "") or "").split())
        if not name:
            continue
        start = getattr(activity, "start", None)
        if isinstance(start, datetime) and start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        return name, start if isinstance(start, datetime) else None
    return None
