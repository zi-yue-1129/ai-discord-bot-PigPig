"""SQLite persistence for the per-guild autoplay taste memory."""

from __future__ import annotations

import sqlite3
import threading
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Tuple, Union

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
"""


class TasteStore:
    """Stores what each guild played, requested and skipped.

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
                    connection.executescript(_SCHEMA)
                    self._ready = True
                with connection:
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
