"""SQLite storage for reminders, so they survive a bot restart."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional, Union

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id TEXT NOT NULL,
    channel_id INTEGER NOT NULL,
    creator_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    created_at REAL NOT NULL,
    due_at REAL NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    repeat TEXT NOT NULL DEFAULT 'none',
    anchor_at REAL
);
CREATE INDEX IF NOT EXISTS idx_reminders_pending ON reminders (status, due_at);
"""

_COLUMNS = "id, guild_id, channel_id, creator_id, target_id, message, created_at, due_at, attempts, repeat, anchor_at"
_FINAL_STATUSES = ("delivered", "failed", "cancelled")

# How far apart a repeating reminder's occurrences are.
REPEAT_INTERVALS = {"daily": 24 * 3600, "weekly": 7 * 24 * 3600}
REPEAT_CHOICES = ("none",) + tuple(REPEAT_INTERVALS)


def next_occurrence(due_at: float, repeat: str, now: float) -> float | None:
    """The first occurrence of a repeating reminder after ``now``, or None when it does not repeat."""
    interval = REPEAT_INTERVALS.get(repeat)
    if interval is None:
        return None
    missed = max(int((now - due_at) // interval) + 1, 1)
    return due_at + missed * interval


@dataclass(frozen=True)
class Reminder:
    """One stored reminder.

    Attributes:
        id: Database ID shown to users for cancelling.
        guild_id: Guild where it was set (``"@me"`` for direct messages).
        channel_id: Channel the reminder is posted to.
        creator_id: User who set it.
        target_id: User to remind.
        message: What to remind about, as the user wrote it.
        created_at: Unix time it was set.
        due_at: Unix time it is due.
        attempts: Failed delivery attempts so far.
        repeat: ``"none"``, ``"daily"`` or ``"weekly"``.
        anchor_at: The first due time; a repeating reminder recurs from it even after a retry moved ``due_at``.
    """

    id: int
    guild_id: str
    channel_id: int
    creator_id: int
    target_id: int
    message: str
    created_at: float
    due_at: float
    attempts: int
    repeat: str = "none"
    anchor_at: Optional[float] = None


class ReminderStore:
    """Reads and writes reminders.

    Database errors are raised to the caller: a reminder that could not be saved must
    not be reported to the user as set.

    Attributes:
        path: The database file.
    """

    def __init__(self, path: Union[str, Path]) -> None:
        """Creates the store; the file and table are created on first use.

        Args:
            path: The SQLite database file.
        """
        self.path = Path(path)
        self._lock = threading.Lock()
        self._ready = False

    @contextmanager
    def _session(self) -> Iterator[sqlite3.Connection]:
        """Yields a connection that commits and closes."""
        with self._lock:
            if not self._ready:
                self.path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.path, timeout=10)
            try:
                if not self._ready:
                    connection.executescript(_SCHEMA)
                    columns = {row[1] for row in connection.execute("PRAGMA table_info(reminders)")}
                    # Databases made before repeating reminders existed.
                    if "repeat" not in columns:
                        connection.execute("ALTER TABLE reminders ADD COLUMN repeat TEXT NOT NULL DEFAULT 'none'")
                    if "anchor_at" not in columns:
                        connection.execute("ALTER TABLE reminders ADD COLUMN anchor_at REAL")
                    self._ready = True
                with connection:
                    yield connection
            finally:
                connection.close()

    def add(
        self, *, guild_id: str, channel_id: int, creator_id: int, target_id: int, message: str,
        created_at: float, due_at: float, repeat: str = "none",
    ) -> int:
        """Stores a new pending reminder and returns its ID."""
        if repeat not in REPEAT_CHOICES:
            raise ValueError(f"Unknown reminder repeat: {repeat}")
        with self._session() as connection:
            cursor = connection.execute(
                "INSERT INTO reminders (guild_id, channel_id, creator_id, target_id, message, created_at, due_at, repeat, anchor_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (guild_id, channel_id, creator_id, target_id, message, created_at, due_at, repeat, due_at),
            )
            return int(cursor.lastrowid)

    def _select(self, where: str, parameters: tuple) -> List[Reminder]:
        """Returns pending reminders matching ``where`` in due order."""
        with self._session() as connection:
            rows = connection.execute(
                f"SELECT {_COLUMNS} FROM reminders WHERE status = 'pending' {where} ORDER BY due_at, id", parameters
            ).fetchall()
        return [Reminder(*row) for row in rows]

    def pending(self) -> List[Reminder]:
        """Returns every pending reminder in due order."""
        return self._select("", ())

    def due(self, now: float) -> List[Reminder]:
        """Returns the pending reminders due at or before ``now``."""
        return self._select("AND due_at <= ?", (now,))

    def list_for_creator(self, creator_id: int) -> List[Reminder]:
        """Returns the pending reminders a user set."""
        return self._select("AND creator_id = ?", (creator_id,))

    def count_pending(self, creator_id: int) -> int:
        """Returns how many pending reminders a user has set."""
        return len(self.list_for_creator(creator_id))

    def list_from_others(self, target_id: int) -> List[Reminder]:
        """Returns the pending reminders other people set for a user."""
        return self._select("AND target_id = ? AND creator_id != ?", (target_id, target_id))

    def count_from_others(self, target_id: int) -> int:
        """Returns how many pending reminders other people have set for a user."""
        return len(self.list_from_others(target_id))

    def cancel(self, reminder_id: int, user_id: int) -> bool:
        """Cancels a pending reminder that ``user_id`` set or that is for ``user_id``.

        Returns:
            Whether a reminder was cancelled.
        """
        with self._session() as connection:
            cursor = connection.execute(
                "UPDATE reminders SET status = 'cancelled' "
                "WHERE id = ? AND (creator_id = ? OR target_id = ?) AND status = 'pending'",
                (reminder_id, user_id, user_id),
            )
            return cursor.rowcount > 0

    def finish(self, reminder_id: int, status: str) -> None:
        """Marks a reminder as ``delivered`` or ``failed``."""
        if status not in _FINAL_STATUSES:
            raise ValueError(f"Unknown reminder status: {status}")
        with self._session() as connection:
            connection.execute("UPDATE reminders SET status = ? WHERE id = ?", (status, reminder_id))

    def postpone(self, reminder_id: int, until: float) -> int:
        """Moves a reminder whose delivery failed to a later time and counts the attempt.

        Returns:
            The number of failed attempts so far.
        """
        with self._session() as connection:
            connection.execute(
                "UPDATE reminders SET due_at = ?, attempts = attempts + 1 WHERE id = ?", (until, reminder_id)
            )
            return int(connection.execute("SELECT attempts FROM reminders WHERE id = ?", (reminder_id,)).fetchone()[0])

    def reschedule(self, reminder_id: int, due_at: float) -> None:
        """Moves a repeating reminder to its next occurrence and clears its failed attempts."""
        with self._session() as connection:
            connection.execute(
                "UPDATE reminders SET due_at = ?, attempts = 0 WHERE id = ? AND status = 'pending'", (due_at, reminder_id)
            )
