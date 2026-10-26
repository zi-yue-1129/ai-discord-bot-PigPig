"""Who is playing which game right now, per server, kept from presence updates.

Only the game's name and when the member started playing are kept, in memory: nothing about
presences is written to disk. Games are grouped by name, ignoring case and spacing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def game_key(name: str) -> str:
    """The name games are grouped by: ``"VALORANT"`` and ``"valorant "`` are the same game."""
    return " ".join(name.split()).casefold()


@dataclass(frozen=True)
class GameGroup:
    """Members who have been playing the same game long enough.

    Attributes:
        key: The game's grouping key (see :func:`game_key`).
        name: The game's name as one of them shows it.
        user_ids: The players, longest playing first.
    """

    key: str
    name: str
    user_ids: List[int]


class PlayingTracker:
    """Each member's current game, per guild."""

    def __init__(self) -> None:
        # guild_id -> user_id -> (game key, game name, playing since as UNIX time)
        self._playing: Dict[int, Dict[int, Tuple[str, str, float]]] = {}

    def update(self, guild_id: int, user_id: int, game: Optional[Tuple[str, Optional[datetime]]], now: float) -> None:
        """Records what a member plays now (``game`` as from ``addons.presence.current_game``).

        A member who keeps playing the same game keeps their start time; a start time Discord
        does not give (or gives in the future) counts from ``now``.
        """
        members = self._playing.setdefault(guild_id, {})
        if game is None:
            members.pop(user_id, None)
            if not members:
                del self._playing[guild_id]
            return
        name, started = game
        key = game_key(name)
        current = members.get(user_id)
        if current is not None and current[0] == key:
            return
        since = started.timestamp() if started is not None else now
        members[user_id] = (key, name, min(since, now))

    def forget_guild(self, guild_id: int) -> None:
        self._playing.pop(guild_id, None)

    def playing(self, guild_id: int, user_id: int) -> Optional[str]:
        """The game key a member is playing in a guild, or None."""
        entry = self._playing.get(guild_id, {}).get(user_id)
        return entry[0] if entry else None

    def groups(self, guild_id: int, now: float, min_seconds: float) -> List[GameGroup]:
        """Games being played by at least one member for ``min_seconds``, most players first."""
        by_game: Dict[str, List[Tuple[float, int, str]]] = {}
        for user_id, (key, name, since) in self._playing.get(guild_id, {}).items():
            if now - since >= min_seconds:
                by_game.setdefault(key, []).append((since, user_id, name))
        groups = []
        for key, players in by_game.items():
            players.sort()
            groups.append(GameGroup(key=key, name=players[0][2], user_ids=[user_id for _, user_id, _ in players]))
        groups.sort(key=lambda group: (-len(group.user_ids), group.key))
        return groups
