"""SQLite storage for community features: per-guild settings, birthdays, daily jobs, opt-outs and achievements."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union

_SCHEMA = """
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER PRIMARY KEY,
    announce_channel_id INTEGER,
    timezone TEXT,
    welcome_enabled INTEGER NOT NULL DEFAULT 0,
    welcome_channel_id INTEGER,
    welcome_note TEXT NOT NULL DEFAULT '',
    farewell_enabled INTEGER NOT NULL DEFAULT 0,
    birthday_enabled INTEGER NOT NULL DEFAULT 0,
    birthday_hour INTEGER NOT NULL DEFAULT 9,
    birthday_role_id INTEGER,
    anniversary_enabled INTEGER NOT NULL DEFAULT 0,
    achievement_mode TEXT NOT NULL DEFAULT 'off',
    weekly_enabled INTEGER NOT NULL DEFAULT 0,
    weekly_channel_id INTEGER,
    weekly_day INTEGER NOT NULL DEFAULT 6,
    weekly_hour INTEGER NOT NULL DEFAULT 20,
    playing_enabled INTEGER NOT NULL DEFAULT 0,
    playing_channel_id INTEGER,
    playing_min_players INTEGER NOT NULL DEFAULT 3
);
CREATE TABLE IF NOT EXISTS birthdays (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE IF NOT EXISTS job_runs (
    guild_id INTEGER NOT NULL,
    job TEXT NOT NULL,
    period TEXT NOT NULL,
    PRIMARY KEY (guild_id, job, period)
);
CREATE TABLE IF NOT EXISTS optouts (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE IF NOT EXISTS user_achievements (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    achievement_id TEXT NOT NULL,
    unlocked_at REAL NOT NULL,
    PRIMARY KEY (guild_id, user_id, achievement_id)
);
CREATE TABLE IF NOT EXISTS titles (
    guild_id INTEGER NOT NULL,
    title_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    period TEXT NOT NULL,
    PRIMARY KEY (guild_id, title_id)
);
CREATE TABLE IF NOT EXISTS game_scores (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    game TEXT NOT NULL,
    points INTEGER NOT NULL,
    played_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_game_scores_guild_time ON game_scores (guild_id, played_at);
CREATE TABLE IF NOT EXISTS achievement_checked (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (guild_id, user_id)
);
CREATE TABLE IF NOT EXISTS playing_posts (
    message_id INTEGER PRIMARY KEY,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    game_key TEXT NOT NULL,
    game TEXT NOT NULL,
    posted_at REAL NOT NULL,
    voice_channel_id INTEGER,
    room_claimed_at REAL,
    sent INTEGER NOT NULL DEFAULT 1,
    room_token TEXT,
    room_used_at REAL
);
CREATE INDEX IF NOT EXISTS idx_playing_posts_guild ON playing_posts (guild_id, posted_at);
CREATE TABLE IF NOT EXISTS temp_voice_rooms (
    channel_id INTEGER PRIMARY KEY,
    guild_id INTEGER NOT NULL,
    created_at REAL NOT NULL,
    post_message_id INTEGER
);
CREATE TABLE IF NOT EXISTS birthday_roles (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    remove_at REAL NOT NULL,
    PRIMARY KEY (guild_id, user_id, role_id)
);
"""

# Columns added after a table first shipped: (table, column, definition).
_ADDED_COLUMNS = [
    # 0 for entries written before the bot skipped members who already had the role: those
    # members may have had it all along, so it is not taken back from them.
    ("birthday_roles", "given_by_bot", "INTEGER NOT NULL DEFAULT 0"),
    ("guild_settings", "achievement_mode", "TEXT NOT NULL DEFAULT 'off'"),
    ("guild_settings", "weekly_enabled", "INTEGER NOT NULL DEFAULT 0"),
    ("guild_settings", "weekly_channel_id", "INTEGER"),
    ("guild_settings", "weekly_day", "INTEGER NOT NULL DEFAULT 6"),
    ("guild_settings", "weekly_hour", "INTEGER NOT NULL DEFAULT 20"),
    ("guild_settings", "playing_enabled", "INTEGER NOT NULL DEFAULT 0"),
    ("guild_settings", "playing_channel_id", "INTEGER"),
    ("guild_settings", "playing_min_players", "INTEGER NOT NULL DEFAULT 3"),
    ("temp_voice_rooms", "post_message_id", "INTEGER"),
    ("playing_posts", "room_claimed_at", "REAL"),
    ("playing_posts", "sent", "INTEGER NOT NULL DEFAULT 1"),
    ("playing_posts", "room_token", "TEXT"),
    ("playing_posts", "room_used_at", "REAL"),
]


@dataclass(frozen=True)
class GuildSettings:
    """One guild's community settings; every feature is off until an admin turns it on.

    Attributes:
        guild_id: The guild.
        announce_channel_id: Default channel for announcements (welcome, birthdays, recaps).
        timezone: IANA time zone name for daily jobs; None uses the bot's default.
        welcome_enabled: Whether new members are welcomed.
        welcome_channel_id: Where welcomes go; None means the announcement channel.
        welcome_note: What the admin wants every welcome to point out (rules channel etc.).
        farewell_enabled: Whether a short line is posted when someone leaves.
        birthday_enabled: Whether birthdays are celebrated.
        birthday_hour: Local hour (0-23) birthday and anniversary messages are posted.
        birthday_role_id: Role given to birthday members for the day, if any.
        anniversary_enabled: Whether yearly join anniversaries are celebrated.
        achievement_mode: How unlocked achievements are announced: ``"off"`` (only shown
            in /profile and /achievements), ``"reply"`` (a reaction and a short reply to the
            message that unlocked it) or ``"channel"`` (a line in the announcement channel).
        weekly_enabled: Whether a weekly recap is posted.
        weekly_channel_id: Channel for the recap; None uses the announcement channel.
        weekly_day: Local weekday the recap is posted (0 Monday ... 6 Sunday).
        weekly_hour: Local hour (0-23) the recap is posted.
        playing_enabled: Whether the bot points out when several members play the same game.
        playing_channel_id: Where those posts go; None uses the announcement channel.
        playing_min_players: How many members must play the same game.
    """

    guild_id: int
    announce_channel_id: Optional[int] = None
    timezone: Optional[str] = None
    welcome_enabled: bool = False
    welcome_channel_id: Optional[int] = None
    welcome_note: str = ""
    farewell_enabled: bool = False
    birthday_enabled: bool = False
    birthday_hour: int = 9
    birthday_role_id: Optional[int] = None
    anniversary_enabled: bool = False
    achievement_mode: str = "off"
    weekly_enabled: bool = False
    weekly_channel_id: Optional[int] = None
    weekly_day: int = 6
    weekly_hour: int = 20
    playing_enabled: bool = False
    playing_channel_id: Optional[int] = None
    playing_min_players: int = 3


_COLUMNS = [f.name for f in fields(GuildSettings)]
_BOOL_COLUMNS = {f.name for f in fields(GuildSettings) if f.type in ("bool", bool)}


class CommunityStore:
    """Keeps community settings and state; the file and tables are created on first use.

    Attributes:
        path: The SQLite database file.
    """

    def __init__(self, path: Union[str, Path]) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._ready = False

    @contextmanager
    def _session(self) -> Iterator[sqlite3.Connection]:
        """Yields a connection (folder and tables created the first time) that commits and closes."""
        with self._lock:
            if not self._ready:
                self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.path, timeout=10)
            try:
                if not self._ready:
                    connection.executescript(_SCHEMA)
                    _add_missing_columns(connection)
                    self._ready = True
                with connection:
                    yield connection
            finally:
                connection.close()

    # ------------------------------------------------------------ settings
    def get_settings(self, guild_id: int) -> GuildSettings:
        """Returns a guild's settings (defaults when it has none)."""
        with self._session() as connection:
            row = connection.execute(
                f"SELECT {', '.join(_COLUMNS)} FROM guild_settings WHERE guild_id = ?", (guild_id,)
            ).fetchone()
        if row is None:
            return GuildSettings(guild_id=guild_id)
        values = {name: (bool(value) if name in _BOOL_COLUMNS else value) for name, value in zip(_COLUMNS, row)}
        return GuildSettings(**values)

    def update_settings(self, guild_id: int, **changes: Any) -> GuildSettings:
        """Changes some of a guild's settings and returns the result.

        Raises:
            TypeError: When a change names an unknown setting.
        """
        settings = replace(self.get_settings(guild_id), **changes)
        values = [getattr(settings, name) for name in _COLUMNS]
        values = [int(value) if isinstance(value, bool) else value for value in values]
        with self._session() as connection:
            connection.execute(
                f"INSERT OR REPLACE INTO guild_settings ({', '.join(_COLUMNS)}) "
                f"VALUES ({', '.join('?' for _ in _COLUMNS)})",
                values,
            )
        return settings

    def guilds_with_daily_jobs(self) -> List[GuildSettings]:
        """Returns the settings of every guild with birthdays, anniversaries or the weekly recap on."""
        with self._session() as connection:
            ids = [
                guild_id
                for (guild_id,) in connection.execute(
                    "SELECT guild_id FROM guild_settings "
                    "WHERE birthday_enabled = 1 OR anniversary_enabled = 1 OR weekly_enabled = 1"
                )
            ]
        return [self.get_settings(guild_id) for guild_id in ids]

    def guilds_with_playing(self) -> List[GuildSettings]:
        """Returns the settings of every guild with "what everyone is playing" on."""
        with self._session() as connection:
            ids = [guild_id for (guild_id,) in connection.execute("SELECT guild_id FROM guild_settings WHERE playing_enabled = 1")]
        return [self.get_settings(guild_id) for guild_id in ids]

    # ------------------------------------------------------------ playing
    def add_playing_post(
        self, guild_id: int, channel_id: int, message_id: int, game_key: str, game: str, now: float, sent: bool = True
    ) -> None:
        """Records a post about members playing ``game`` (for the cooldown, the daily cap and its button).

        ``sent=False`` records it just before it is sent; :meth:`move_playing_post` marks it sent.
        """
        with self._session() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO playing_posts (message_id, guild_id, channel_id, game_key, game, posted_at, sent)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (message_id, guild_id, channel_id, game_key, game, now, int(sent)),
            )

    def forget_unsent_playing_posts(self, before: float) -> None:
        """Drops posts recorded before ``before`` for a send that never finished."""
        with self._session() as connection:
            connection.execute("DELETE FROM playing_posts WHERE sent = 0 AND posted_at < ?", (before,))

    def last_playing_post(self, guild_id: int, game_key: str) -> Optional[float]:
        """When the guild last got a post about this game, or None."""
        with self._session() as connection:
            row = connection.execute(
                "SELECT MAX(posted_at) FROM playing_posts WHERE guild_id = ? AND game_key = ?", (guild_id, game_key)
            ).fetchone()
        return row[0] if row and row[0] is not None else None

    def count_playing_posts(self, guild_id: int, since: float) -> int:
        with self._session() as connection:
            return int(
                connection.execute(
                    "SELECT COUNT(*) FROM playing_posts WHERE guild_id = ? AND posted_at >= ?", (guild_id, since)
                ).fetchone()[0]
            )

    def playing_post(self, message_id: int) -> Optional[Dict[str, Any]]:
        """The post with this message, as a dict of its columns, or None."""
        with self._session() as connection:
            row = connection.execute(
                "SELECT message_id, guild_id, channel_id, game_key, game, posted_at, voice_channel_id,"
                " room_claimed_at, room_used_at FROM playing_posts WHERE message_id = ?",
                (message_id,),
            ).fetchone()
        if row is None:
            return None
        keys = (
            "message_id", "guild_id", "channel_id", "game_key", "game", "posted_at", "voice_channel_id",
            "room_claimed_at", "room_used_at",
        )
        return dict(zip(keys, row))

    def move_playing_post(self, old_message_id: int, message_id: int) -> None:
        """Gives a post recorded before it was sent its real message id, and marks it sent."""
        with self._session() as connection:
            connection.execute(
                "UPDATE playing_posts SET message_id = ?, sent = 1 WHERE message_id = ?", (message_id, old_message_id)
            )

    def forget_playing_post(self, message_id: int) -> None:
        with self._session() as connection:
            connection.execute("DELETE FROM playing_posts WHERE message_id = ?", (message_id,))

    def claim_playing_post(
        self, message_id: int, rooms_open: int, max_rooms: int, now: float, token: Optional[str] = None
    ) -> bool:
        """Marks a post as opening its room (``voice_channel_id`` -1 until the room is known), under
        ``token``, which only the press that made the claim knows.

        Returns False when the post already opened one (or is opening one), or when ``rooms_open``
        plus the rooms other posts of the guild are opening right now reach ``max_rooms``: one
        statement decides both.
        """
        with self._session() as connection:
            cursor = connection.execute(
                "UPDATE playing_posts SET voice_channel_id = -1, room_claimed_at = ?, room_token = ?"
                " WHERE message_id = ? AND voice_channel_id IS NULL AND room_used_at IS NULL AND ? + ("
                "  SELECT COUNT(*) FROM playing_posts AS other"
                "  WHERE other.guild_id = playing_posts.guild_id AND other.voice_channel_id = -1"
                "  AND other.message_id NOT IN (SELECT post_message_id FROM temp_voice_rooms WHERE post_message_id IS NOT NULL)"
                " ) < ?",
                (now, token, message_id, rooms_open, max_rooms),
            )
            return cursor.rowcount == 1

    def confirm_playing_room(self, message_id: int, token: Optional[str], now: float) -> bool:
        """Marks a post used for good once its room exists; nothing ever clears this.

        Returns False when the claim is no longer ``token``'s (it was freed and claimed again).
        """
        with self._session() as connection:
            cursor = connection.execute(
                "UPDATE playing_posts SET room_used_at = ?"
                " WHERE message_id = ? AND room_token IS ? AND voice_channel_id = -1 AND room_used_at IS NULL",
                (now, message_id, token),
            )
            return cursor.rowcount == 1

    def open_claims(self, guild_id: int) -> List[Tuple[int, str, Optional[float], Optional[float]]]:
        """``(message_id, token, claimed_at, used_at)`` of the guild's claims whose room is not on record.

        A claim that was marked used (its room exists) but whose room could not be recorded is
        included: its token is all that is left to find the room by.
        """
        with self._session() as connection:
            return connection.execute(
                "SELECT message_id, room_token, room_claimed_at, room_used_at FROM playing_posts"
                " WHERE guild_id = ? AND voice_channel_id = -1 AND room_token IS NOT NULL",
                (guild_id,),
            ).fetchall()

    def mark_playing_post_sent(self, message_id: int) -> None:
        with self._session() as connection:
            connection.execute("UPDATE playing_posts SET sent = 1 WHERE message_id = ?", (message_id,))

    def release_stale_claims(self, before: float, keep: Iterable[int] = ()) -> None:
        """Frees claims made before ``before`` (or at an unknown time) that never got a room, except
        the posts in ``keep``."""
        keep = list(keep)
        marks = ",".join("?" * len(keep))
        with self._session() as connection:
            connection.execute(
                "UPDATE playing_posts SET voice_channel_id = NULL, room_token = NULL"
                " WHERE voice_channel_id = -1 AND (room_claimed_at IS NULL OR room_claimed_at < ?)"
                " AND message_id NOT IN (SELECT post_message_id FROM temp_voice_rooms WHERE post_message_id IS NOT NULL)"
                + (f" AND message_id NOT IN ({marks})" if keep else ""),
                (before, *keep),
            )

    def playing_rooms(self, guild_id: Optional[int] = None) -> List[Tuple[int, int, float]]:
        """``(guild_id, channel_id, claimed_at)`` for every room a post points to."""
        query = "SELECT guild_id, voice_channel_id, COALESCE(room_claimed_at, posted_at) FROM playing_posts WHERE voice_channel_id > 0"
        with self._session() as connection:
            if guild_id is None:
                return connection.execute(query).fetchall()
            return connection.execute(query + " AND guild_id = ?", (guild_id,)).fetchall()

    def release_playing_post(self, message_id: int, token: Optional[str] = None) -> None:
        """Takes back ``token``'s claim, whose room could not be created (or was taken back)."""
        with self._session() as connection:
            connection.execute(
                "UPDATE playing_posts SET voice_channel_id = NULL, room_token = NULL"
                " WHERE message_id = ? AND voice_channel_id = -1 AND room_token IS ?",
                (message_id, token),
            )

    def set_playing_voice(self, message_id: int, voice_channel_id: int) -> None:
        with self._session() as connection:
            connection.execute(
                "UPDATE playing_posts SET voice_channel_id = ? WHERE message_id = ?", (voice_channel_id, message_id)
            )

    def forget_playing_posts(self, before: float, keep: Iterable[int] = ()) -> None:
        """Drops posts older than ``before`` (they no longer count for anything), except the posts in
        ``keep``: their room still has to be found or deleted."""
        keep = list(keep)
        marks = ",".join("?" * len(keep))
        with self._session() as connection:
            connection.execute(
                "DELETE FROM playing_posts WHERE posted_at < ?" + (f" AND message_id NOT IN ({marks})" if keep else ""),
                (before, *keep),
            )

    def add_temp_voice(self, guild_id: int, channel_id: int, now: float, post_message_id: Optional[int] = None) -> None:
        """Remembers a voice room the bot made (and the post it was opened from), so it is deleted once empty."""
        with self._session() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO temp_voice_rooms (channel_id, guild_id, created_at, post_message_id) VALUES (?, ?, ?, ?)",
                (channel_id, guild_id, now, post_message_id),
            )

    def temp_voice_for_post(self, post_message_id: int) -> Optional[int]:
        """The recorded room a post opened, or None."""
        with self._session() as connection:
            row = connection.execute(
                "SELECT channel_id FROM temp_voice_rooms WHERE post_message_id = ?", (post_message_id,)
            ).fetchone()
        return row[0] if row else None

    def temp_voice_rooms(self, guild_id: Optional[int] = None) -> List[Tuple[int, int, float]]:
        """Returns ``(guild_id, channel_id, created_at)`` for the bot's voice rooms (of one guild, if given)."""
        with self._session() as connection:
            if guild_id is None:
                return connection.execute("SELECT guild_id, channel_id, created_at FROM temp_voice_rooms").fetchall()
            return connection.execute(
                "SELECT guild_id, channel_id, created_at FROM temp_voice_rooms WHERE guild_id = ?", (guild_id,)
            ).fetchall()

    def is_temp_voice(self, channel_id: int) -> bool:
        with self._session() as connection:
            return connection.execute("SELECT 1 FROM temp_voice_rooms WHERE channel_id = ?", (channel_id,)).fetchone() is not None

    def forget_temp_voice(self, channel_id: int) -> None:
        with self._session() as connection:
            connection.execute("DELETE FROM temp_voice_rooms WHERE channel_id = ?", (channel_id,))

    # ------------------------------------------------------------ birthdays
    def set_birthday(self, guild_id: int, user_id: int, month: int, day: int) -> None:
        """Saves (or replaces) a member's birthday in one guild."""
        with self._session() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO birthdays (guild_id, user_id, month, day) VALUES (?, ?, ?, ?)",
                (guild_id, user_id, month, day),
            )

    def remove_birthday(self, guild_id: int, user_id: int) -> bool:
        """Deletes a member's birthday in one guild; returns whether one was saved."""
        with self._session() as connection:
            cursor = connection.execute("DELETE FROM birthdays WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
            return cursor.rowcount > 0

    def get_birthday(self, guild_id: int, user_id: int) -> Optional[Tuple[int, int]]:
        """Returns a member's ``(month, day)`` in one guild, or None."""
        with self._session() as connection:
            row = connection.execute(
                "SELECT month, day FROM birthdays WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
            ).fetchone()
        return (row[0], row[1]) if row else None

    def birthdays(self, guild_id: int) -> List[Tuple[int, int, int]]:
        """Returns every ``(user_id, month, day)`` saved in a guild."""
        with self._session() as connection:
            return connection.execute(
                "SELECT user_id, month, day FROM birthdays WHERE guild_id = ? ORDER BY month, day", (guild_id,)
            ).fetchall()

    # ------------------------------------------------------------ job runs
    def has_run(self, guild_id: int, job: str, period: str) -> bool:
        """Whether a job was already marked done for a period (see ``claim_run``)."""
        with self._session() as connection:
            row = connection.execute(
                "SELECT 1 FROM job_runs WHERE guild_id = ? AND job = ? AND period = ?", (guild_id, job, period)
            ).fetchone()
            return row is not None

    def claim_run(self, guild_id: int, job: str, period: str) -> bool:
        """Marks a job as done for a period; returns False when it already was (so it runs once).

        Args:
            guild_id: The guild.
            job: The job's name, e.g. ``"birthday"``.
            period: The period it ran for, e.g. a local date ``"2026-10-25"``.
        """
        with self._session() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO job_runs (guild_id, job, period) VALUES (?, ?, ?)", (guild_id, job, period)
            )
            return cursor.rowcount > 0

    # ------------------------------------------------------------ opt-outs
    def set_optout(self, guild_id: int, user_id: int, opted_out: bool) -> None:
        """Hides (or shows again) a member in rankings, recaps and achievement announcements."""
        with self._session() as connection:
            if opted_out:
                connection.execute("INSERT OR IGNORE INTO optouts (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
            else:
                connection.execute("DELETE FROM optouts WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))

    def optouts(self, guild_id: int) -> Set[int]:
        """Returns the IDs of a guild's members who opted out."""
        with self._session() as connection:
            return {user_id for (user_id,) in connection.execute("SELECT user_id FROM optouts WHERE guild_id = ?", (guild_id,))}

    def is_opted_out(self, guild_id: int, user_id: int) -> bool:
        return user_id in self.optouts(guild_id)

    # ------------------------------------------------------------ achievements
    def unlock(self, guild_id: int, user_id: int, achievement_ids: List[str], now: float) -> List[str]:
        """Records achievements; returns the ones that were newly unlocked, in the given order."""
        new: List[str] = []
        with self._session() as connection:
            for achievement_id in achievement_ids:
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO user_achievements (guild_id, user_id, achievement_id, unlocked_at) "
                    "VALUES (?, ?, ?, ?)",
                    (guild_id, user_id, achievement_id, now),
                )
                if cursor.rowcount > 0:
                    new.append(achievement_id)
        return new

    def was_checked(self, guild_id: int, user_id: int) -> bool:
        """Whether a member's achievements were checked before (so earlier progress is already recorded)."""
        with self._session() as connection:
            row = connection.execute(
                "SELECT 1 FROM achievement_checked WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
            ).fetchone()
            return row is not None

    def mark_checked(self, guild_id: int, user_id: int) -> None:
        with self._session() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO achievement_checked (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id)
            )

    def achievements(self, guild_id: int, user_id: int) -> List[Tuple[str, float]]:
        """Returns a member's ``(achievement_id, unlocked_at)`` pairs, oldest first."""
        with self._session() as connection:
            return connection.execute(
                "SELECT achievement_id, unlocked_at FROM user_achievements WHERE guild_id = ? AND user_id = ? "
                "ORDER BY unlocked_at, achievement_id",
                (guild_id, user_id),
            ).fetchall()

    # ------------------------------------------------------------ titles
    def set_titles(self, guild_id: int, period: str, holders: Dict[str, int]) -> None:
        """Replaces a guild's rotating titles with this period's ``{title_id: user_id}``."""
        with self._session() as connection:
            connection.execute("DELETE FROM titles WHERE guild_id = ?", (guild_id,))
            connection.executemany(
                "INSERT INTO titles (guild_id, title_id, user_id, period) VALUES (?, ?, ?, ?)",
                [(guild_id, title_id, user_id, period) for title_id, user_id in holders.items()],
            )

    def titles_of(self, guild_id: int, user_id: int) -> List[str]:
        """Returns the rotating titles a member holds now."""
        with self._session() as connection:
            return [
                title_id
                for (title_id,) in connection.execute(
                    "SELECT title_id FROM titles WHERE guild_id = ? AND user_id = ? ORDER BY title_id", (guild_id, user_id)
                )
            ]

    # ------------------------------------------------------------ games
    def add_game_scores(self, guild_id: int, game: str, points: Dict[int, int], played_at: float) -> None:
        """Records one finished game's points per player (players with 0 points are kept out)."""
        with self._session() as connection:
            connection.executemany(
                "INSERT INTO game_scores (guild_id, user_id, game, points, played_at) VALUES (?, ?, ?, ?, ?)",
                [(guild_id, user_id, game, value, played_at) for user_id, value in points.items() if value > 0],
            )

    def game_points(self, guild_id: int, since: float = 0, until: float = float("inf")) -> List[Tuple[int, int]]:
        """Returns each player's game points in a time range, as ``(user_id, points)``, most first."""
        with self._session() as connection:
            return connection.execute(
                "SELECT user_id, SUM(points) AS total FROM game_scores WHERE guild_id = ? AND played_at >= ? AND played_at < ? "
                "GROUP BY user_id ORDER BY total DESC, user_id",
                (guild_id, since, until if until != float("inf") else 1e18),
            ).fetchall()

    # ------------------------------------------------------------ birthday roles
    def add_birthday_role(self, guild_id: int, user_id: int, role_id: int, remove_at: float) -> None:
        """Remembers to take a birthday role back at ``remove_at`` (UNIX time)."""
        with self._session() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO birthday_roles (guild_id, user_id, role_id, remove_at, given_by_bot) VALUES (?, ?, ?, ?, 1)",
                (guild_id, user_id, role_id, remove_at),
            )

    def due_birthday_roles(self, now: float) -> List[Tuple[int, int, int, bool]]:
        """Returns ``(guild_id, user_id, role_id, given_by_bot)`` for birthday roles that should be taken back.

        ``given_by_bot`` is False for entries from before the bot checked whether the member
        already had the role; those are dropped without taking the role away.
        """
        with self._session() as connection:
            rows = connection.execute(
                "SELECT guild_id, user_id, role_id, given_by_bot FROM birthday_roles WHERE remove_at <= ?", (now,)
            ).fetchall()
        return [(guild_id, user_id, role_id, bool(given)) for guild_id, user_id, role_id, given in rows]

    def forget_birthday_role(self, guild_id: int, user_id: int, role_id: int) -> None:
        """Drops a birthday role entry once it has been taken back (or cannot be)."""
        with self._session() as connection:
            connection.execute(
                "DELETE FROM birthday_roles WHERE guild_id = ? AND user_id = ? AND role_id = ?",
                (guild_id, user_id, role_id),
            )


def _add_missing_columns(connection: sqlite3.Connection) -> None:
    """Adds columns introduced after a database was created (older files keep working)."""
    for table, column, definition in _ADDED_COLUMNS:
        existing = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        if column not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            if (table, column) == ("playing_posts", "room_used_at"):
                # Posts that already opened a room (as far as an older file shows) stay used.
                connection.execute(
                    "UPDATE playing_posts SET room_used_at = posted_at WHERE voice_channel_id IS NOT NULL"
                    " OR message_id IN (SELECT post_message_id FROM temp_voice_rooms WHERE post_message_id IS NOT NULL)"
                )
