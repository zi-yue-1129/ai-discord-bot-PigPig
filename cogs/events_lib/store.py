"""SQLite storage for events (揪團): the event, who signed up, and whether the reminder went out.

Sign-ups are kept in the order people joined. With a limit, the first ``capacity`` people going
are in and the rest wait; when someone leaves, the first person waiting moves up on their own,
because the roster is worked out from that order each time it is read.
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional, Union

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    message_id INTEGER,
    creator_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    starts_at REAL NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 0,
    remind_minutes INTEGER NOT NULL DEFAULT 15,
    status TEXT NOT NULL DEFAULT 'open',
    attempts INTEGER NOT NULL DEFAULT 0,
    next_try_at REAL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_open ON events (status, starts_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_events_message ON events (message_id);
CREATE TABLE IF NOT EXISTS event_signups (
    event_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    joined_at REAL NOT NULL,
    seq INTEGER NOT NULL,
    PRIMARY KEY (event_id, user_id)
);
"""

_COLUMNS = (
    "id, guild_id, channel_id, message_id, creator_id, title, starts_at, capacity, remind_minutes, status, attempts"
)
# When the reminder is (next) tried: its time, or after a failure the retry time.
_TRY_AT = "COALESCE(next_try_at, starts_at - remind_minutes * 60)"
GOING, MAYBE = "going", "maybe"
# open: waiting for the reminder; reminded: the reminder went out (or gave up); cancelled.
OPEN, REMINDED, CANCELLED = "open", "reminded", "cancelled"


@dataclass(frozen=True)
class Event:
    id: int
    guild_id: int
    channel_id: int
    message_id: Optional[int]
    creator_id: int
    title: str
    starts_at: float
    capacity: int
    remind_minutes: int
    status: str
    attempts: int

    @property
    def remind_at(self) -> float:
        return self.starts_at - self.remind_minutes * 60


@dataclass
class Roster:
    """Who is in, who is waiting and who might come, each in the order they signed up."""

    going: List[int] = field(default_factory=list)
    waiting: List[int] = field(default_factory=list)
    maybe: List[int] = field(default_factory=list)


class EventStore:
    """Reads and writes events. Every method is one short transaction, safe across threads."""

    def __init__(self, path: Union[str, Path]) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        with self._session() as db:
            db.executescript(_SCHEMA)

    @contextmanager
    def _session(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            try:
                yield self._connection
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    # ---------------------------------------------------------------- events
    def add(
        self,
        guild_id: int,
        channel_id: int,
        creator_id: int,
        title: str,
        starts_at: float,
        capacity: int,
        remind_minutes: int,
        now: float,
    ) -> int:
        with self._session() as db:
            cursor = db.execute(
                "INSERT INTO events (guild_id, channel_id, creator_id, title, starts_at, capacity, remind_minutes, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (guild_id, channel_id, creator_id, title, starts_at, capacity, remind_minutes, now),
            )
            return int(cursor.lastrowid)

    def set_message(self, event_id: int, message_id: int) -> None:
        with self._session() as db:
            db.execute("UPDATE events SET message_id = ? WHERE id = ?", (message_id, event_id))

    def delete(self, event_id: int) -> None:
        """Removes an event whose message could not be posted."""
        with self._session() as db:
            db.execute("DELETE FROM event_signups WHERE event_id = ?", (event_id,))
            db.execute("DELETE FROM events WHERE id = ?", (event_id,))

    def _select(self, where: str, parameters: tuple) -> List[Event]:
        with self._session() as db:
            rows = db.execute(f"SELECT {_COLUMNS} FROM events WHERE {where}", parameters).fetchall()
        return [Event(*row) for row in rows]

    def get(self, event_id: int) -> Optional[Event]:
        found = self._select("id = ?", (event_id,))
        return found[0] if found else None

    def by_message(self, message_id: int) -> Optional[Event]:
        found = self._select("message_id = ?", (message_id,))
        return found[0] if found else None

    def upcoming(self, guild_id: int, now: float) -> List[Event]:
        return self._select(
            "guild_id = ? AND status != ? AND starts_at > ? ORDER BY starts_at", (guild_id, CANCELLED, now)
        )

    def count_upcoming(self, guild_id: int, now: float, creator_id: Optional[int] = None) -> int:
        query = "SELECT COUNT(*) FROM events WHERE guild_id = ? AND status != ? AND starts_at > ?"
        parameters: tuple = (guild_id, CANCELLED, now)
        if creator_id is not None:
            query += " AND creator_id = ?"
            parameters += (creator_id,)
        with self._session() as db:
            return int(db.execute(query, parameters).fetchone()[0])

    def due_reminders(self, now: float) -> List[Event]:
        """Open events whose reminder time has come (posted ones only)."""
        return self._select(
            f"status = ? AND message_id IS NOT NULL AND {_TRY_AT} <= ? ORDER BY starts_at",
            (OPEN, now),
        )

    def next_reminder_at(self) -> Optional[float]:
        with self._session() as db:
            row = db.execute(
                f"SELECT MIN({_TRY_AT}) FROM events WHERE status = ? AND message_id IS NOT NULL",
                (OPEN,),
            ).fetchone()
        return row[0] if row and row[0] is not None else None

    def mark_reminded(self, event_id: int) -> None:
        with self._session() as db:
            db.execute("UPDATE events SET status = ? WHERE id = ? AND status = ?", (REMINDED, event_id, OPEN))

    def record_failure(self, event_id: int, retry_at: float) -> int:
        """Counts a failed reminder and tries again at ``retry_at``; returns the attempts so far."""
        with self._session() as db:
            db.execute("UPDATE events SET attempts = attempts + 1, next_try_at = ? WHERE id = ?", (retry_at, event_id))
            return int(db.execute("SELECT attempts FROM events WHERE id = ?", (event_id,)).fetchone()[0])

    def cancel(self, event_id: int) -> bool:
        with self._session() as db:
            cursor = db.execute(
                "UPDATE events SET status = ? WHERE id = ? AND status != ?", (CANCELLED, event_id, CANCELLED)
            )
            return cursor.rowcount > 0

    # --------------------------------------------------------------- sign-ups
    def sign_up(self, event_id: int, user_id: int, status: str, now: float) -> None:
        """Sets ``user_id``'s answer. Switching between going and maybe keeps no place in the queue:
        whoever answers "going" last is last in line."""
        with self._session() as db:
            row = db.execute(
                "SELECT status FROM event_signups WHERE event_id = ? AND user_id = ?", (event_id, user_id)
            ).fetchone()
            if row is not None and row[0] == status:
                return
            seq = db.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 FROM event_signups WHERE event_id = ?", (event_id,)
            ).fetchone()[0]
            db.execute(
                "INSERT INTO event_signups (event_id, user_id, status, joined_at, seq) VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT (event_id, user_id) DO UPDATE SET status = excluded.status,"
                " joined_at = excluded.joined_at, seq = excluded.seq",
                (event_id, user_id, status, now, seq),
            )

    def leave(self, event_id: int, user_id: int) -> bool:
        with self._session() as db:
            cursor = db.execute("DELETE FROM event_signups WHERE event_id = ? AND user_id = ?", (event_id, user_id))
            return cursor.rowcount > 0

    def roster(self, event: Event) -> Roster:
        with self._session() as db:
            rows = db.execute(
                "SELECT user_id, status FROM event_signups WHERE event_id = ? ORDER BY seq", (event.id,)
            ).fetchall()
        roster = Roster()
        for user_id, status in rows:
            if status == MAYBE:
                roster.maybe.append(user_id)
            elif event.capacity and len(roster.going) >= event.capacity:
                roster.waiting.append(user_id)
            else:
                roster.going.append(user_id)
        return roster
