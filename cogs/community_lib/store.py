"""SQLite storage for community features: per-guild settings, birthdays, daily jobs, opt-outs and achievements."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any, Iterator, List, Optional, Set, Tuple, Union

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
    achievement_mode TEXT NOT NULL DEFAULT 'off'
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
CREATE TABLE IF NOT EXISTS achievement_checked (
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (guild_id, user_id)
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
    ("guild_settings", "achievement_mode", "TEXT NOT NULL DEFAULT 'off'"),
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
        """Returns the settings of every guild that celebrates birthdays or anniversaries."""
        with self._session() as connection:
            ids = [
                guild_id
                for (guild_id,) in connection.execute(
                    "SELECT guild_id FROM guild_settings WHERE birthday_enabled = 1 OR anniversary_enabled = 1"
                )
            ]
        return [self.get_settings(guild_id) for guild_id in ids]

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

    # ------------------------------------------------------------ birthday roles
    def add_birthday_role(self, guild_id: int, user_id: int, role_id: int, remove_at: float) -> None:
        """Remembers to take a birthday role back at ``remove_at`` (UNIX time)."""
        with self._session() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO birthday_roles (guild_id, user_id, role_id, remove_at) VALUES (?, ?, ?, ?)",
                (guild_id, user_id, role_id, remove_at),
            )

    def due_birthday_roles(self, now: float) -> List[Tuple[int, int, int]]:
        """Returns ``(guild_id, user_id, role_id)`` for birthday roles that should be taken back."""
        with self._session() as connection:
            return connection.execute(
                "SELECT guild_id, user_id, role_id FROM birthday_roles WHERE remove_at <= ?", (now,)
            ).fetchall()

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
