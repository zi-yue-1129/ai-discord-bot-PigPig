"""SQLite persistence for the per-guild autoplay taste memory and the log of played songs."""

from __future__ import annotations

import sqlite3
import threading
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union

from addons.logging import get_logger

log = get_logger(server_id="Bot", source=__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS taste_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    video_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_taste_history_guild ON taste_history (guild_id, id);
CREATE TABLE IF NOT EXISTS taste_author (
    guild_id INTEGER NOT NULL,
    author TEXT NOT NULL,
    requested INTEGER NOT NULL DEFAULT 0,
    skipped INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, author)
);
CREATE TABLE IF NOT EXISTS play_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    video_id TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    requester_id INTEGER,
    autoplay INTEGER NOT NULL DEFAULT 0,
    played_at REAL NOT NULL,
    skipped INTEGER NOT NULL DEFAULT 0,
    listened_seconds REAL,
    text_channel_id INTEGER,
    voice_channel_id INTEGER
);
CREATE INDEX IF NOT EXISTS idx_play_events_guild_time ON play_events (guild_id, played_at);
"""

# Columns added to play_events after it was first released (name, type), added on open when missing.
_PLAY_EVENT_COLUMNS = (("text_channel_id", "INTEGER"), ("voice_channel_id", "INTEGER"))

# Played songs older than this are deleted (they only feed weekly and monthly charts).
PLAY_EVENTS_KEEP_SECONDS = 180 * 24 * 3600


class TasteStore:
    """Stores what each guild played, requested and skipped, and a dated log of played songs.

    A database problem is logged and never interrupts playback: the in-memory taste keeps
    working and only the persistence of that change is lost.

    Attributes:
        path: The database file.
    """

    def __init__(self, path: Union[str, Path]) -> None:
        """Creates the store; the file and tables are created on first use.

        Args:
            path: The SQLite database file.
        """
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
                    # WAL: a long chart read on a worker thread never makes the player's writes wait.
                    connection.execute("PRAGMA journal_mode=WAL")
                    connection.executescript(_SCHEMA)
                    _add_missing_columns(connection)
                    self._ready = True
                with connection:
                    yield connection
            finally:
                connection.close()

    @contextmanager
    def _reader(self) -> Iterator[sqlite3.Connection]:
        """Yields a connection for reading only, without the store's lock.

        Chart reads run on worker threads and may be slow; holding the lock would make the
        player's writes on the event loop wait for them. The database is in WAL mode, so the
        read does not block writers in SQLite either.
        """
        if not self._ready:
            with self._session():
                pass
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            yield connection
        finally:
            connection.close()

    def load(self, guild_id: int, history_size: int) -> Tuple[List[str], Counter, Counter]:
        """Reads a guild's saved taste.

        Args:
            guild_id: The guild.
            history_size: How many of the most recent played songs to return.

        Returns:
            ``(video_ids oldest first, requested counts, skipped counts)``; empty when the
            database cannot be read.
        """
        requested: Counter = Counter()
        skipped: Counter = Counter()
        try:
            with self._session() as connection:
                rows = connection.execute(
                    "SELECT video_id FROM taste_history WHERE guild_id = ? ORDER BY id DESC LIMIT ?",
                    (guild_id, history_size),
                ).fetchall()
                for author, requests, skips in connection.execute(
                    "SELECT author, requested, skipped FROM taste_author WHERE guild_id = ?", (guild_id,)
                ):
                    requested[author] = requests
                    skipped[author] = skips
        except (sqlite3.Error, OSError):
            # Playback must go on without saved taste; the failure is reported here.
            log.error(f"Could not read the autoplay taste from {self.path}", exc_info=True)
            return [], Counter(), Counter()
        return [video_id for (video_id,) in reversed(rows)], requested, skipped

    def add_played(self, guild_id: int, video_id: str, keep: int) -> None:
        """Records a played song and trims the guild's history to ``keep`` songs."""
        self._write(
            [
                ("INSERT INTO taste_history (guild_id, video_id) VALUES (?, ?)", (guild_id, video_id)),
                (
                    "DELETE FROM taste_history WHERE guild_id = ? AND id NOT IN "
                    "(SELECT id FROM taste_history WHERE guild_id = ? ORDER BY id DESC LIMIT ?)",
                    (guild_id, guild_id, keep),
                ),
            ]
        )

    def add_request(self, guild_id: int, author: str) -> None:
        """Counts a request for a song by a (normalized) author."""
        self._bump(guild_id, author, "requested")

    def add_skip(self, guild_id: int, author: str) -> None:
        """Counts a quickly skipped recommendation by a (normalized) author."""
        self._bump(guild_id, author, "skipped")

    def add_play_event(
        self,
        guild_id: int,
        video_id: str,
        title: str,
        requester_id: Optional[int],
        autoplay: bool,
        played_at: Optional[float] = None,
        text_channel_id: Optional[int] = None,
        voice_channel_id: Optional[int] = None,
    ) -> Optional[int]:
        """Logs that a song started playing and drops log entries past the kept period.

        Args:
            guild_id: The guild.
            video_id: The song's video ID.
            title: The song's title.
            requester_id: Who queued it (``None`` when unknown).
            autoplay: Whether autoplay picked it rather than a person.
            played_at: When it started (UNIX time; defaults to now).
            text_channel_id: The channel the player posts in (where it was asked for).
            voice_channel_id: The voice channel it plays in.

        Returns:
            The entry's ID (for ``mark_play_skipped``), or None when it could not be saved.
        """
        played_at = time.time() if played_at is None else played_at
        try:
            with self._session() as connection:
                cursor = connection.execute(
                    "INSERT INTO play_events "
                    "(guild_id, video_id, title, requester_id, autoplay, played_at, text_channel_id, voice_channel_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (guild_id, video_id, title, requester_id, int(autoplay), played_at, text_channel_id, voice_channel_id),
                )
                connection.execute(
                    "DELETE FROM play_events WHERE played_at < ?", (played_at - PLAY_EVENTS_KEEP_SECONDS,)
                )
                return cursor.lastrowid
        except (sqlite3.Error, OSError):
            # Charts only lose this one song; playback is unaffected.
            log.error(f"Could not log a played song to {self.path}", exc_info=True)
            return None

    def mark_play_skipped(self, event_id: int, listened_seconds: float) -> None:
        """Marks a logged song as skipped after ``listened_seconds`` of playback."""
        self._write(
            [("UPDATE play_events SET skipped = 1, listened_seconds = ? WHERE id = ?", (listened_seconds, event_id))]
        )

    def top_played(self, guild_id: int, since: float, until: float, limit: int = 10) -> List[Tuple[str, str, int, int]]:
        """Returns a guild's most played songs in a time range.

        Args:
            guild_id: The guild.
            since: Range start (UNIX time, inclusive).
            until: Range end (UNIX time, exclusive).
            limit: How many songs to return.

        Returns:
            ``(video_id, title, plays, skips)`` tuples, most played first.
        """
        with self._reader() as connection:
            return connection.execute(
                "SELECT video_id, MAX(title), COUNT(*) AS plays, SUM(skipped) FROM play_events "
                "WHERE guild_id = ? AND played_at >= ? AND played_at < ? "
                "GROUP BY video_id ORDER BY plays DESC, MAX(played_at) DESC LIMIT ?",
                (guild_id, since, until, limit),
            ).fetchall()

    def plays_with_places(self, guild_id: int, since: float, until: float, limit: int = 20000) -> List[Tuple]:
        """Returns a guild's played songs in a time range with who asked for them and where, newest first.

        Returns:
            ``(video_id, title, requester_id, skipped, text_channel_id, voice_channel_id)`` tuples;
            the channels are None for songs logged before they were recorded.
        """
        with self._reader() as connection:
            return connection.execute(
                "SELECT video_id, title, requester_id, skipped, text_channel_id, voice_channel_id FROM play_events "
                "WHERE guild_id = ? AND played_at >= ? AND played_at < ? ORDER BY played_at DESC LIMIT ?",
                (guild_id, since, until, limit),
            ).fetchall()

    def top_requesters(self, guild_id: int, since: float, until: float, limit: int = 10) -> List[Tuple[int, int]]:
        """Returns who requested the most songs in a guild in a time range, as ``(user_id, plays)``."""
        with self._session() as connection:
            return connection.execute(
                "SELECT requester_id, COUNT(*) AS plays FROM play_events "
                "WHERE guild_id = ? AND played_at >= ? AND played_at < ? AND requester_id IS NOT NULL AND autoplay = 0 "
                "GROUP BY requester_id ORDER BY plays DESC, requester_id LIMIT ?",
                (guild_id, since, until, limit),
            ).fetchall()

    def history_row_count(self, guild_id: int) -> int:
        """Returns how many played songs are stored for a guild."""
        with self._session() as connection:
            return connection.execute("SELECT COUNT(*) FROM taste_history WHERE guild_id = ?", (guild_id,)).fetchone()[0]

    def _bump(self, guild_id: int, author: str, column: str) -> None:
        """Increments one author counter (``column`` is one of two fixed names)."""
        if column not in ("requested", "skipped"):
            raise ValueError(f"Unknown taste column: {column}")
        self._write(
            [
                (
                    f"INSERT INTO taste_author (guild_id, author, {column}) VALUES (?, ?, 1) "
                    f"ON CONFLICT (guild_id, author) DO UPDATE SET {column} = {column} + 1",
                    (guild_id, author),
                )
            ]
        )

    def _write(self, statements: List[Tuple[str, tuple]]) -> None:
        """Runs statements in one transaction, logging (not raising) database failures."""
        try:
            with self._session() as connection:
                for statement, parameters in statements:
                    connection.execute(statement, parameters)
        except (sqlite3.Error, OSError):
            # The in-memory taste already has this change; only its persistence is lost.
            log.error(f"Could not save the autoplay taste to {self.path}", exc_info=True)


def _add_missing_columns(connection: sqlite3.Connection) -> None:
    """Adds the play log columns an older database file does not have yet."""
    present = {row[1] for row in connection.execute("PRAGMA table_info(play_events)")}
    for name, kind in _PLAY_EVENT_COLUMNS:
        if name not in present:
            connection.execute(f"ALTER TABLE play_events ADD COLUMN {name} {kind}")
