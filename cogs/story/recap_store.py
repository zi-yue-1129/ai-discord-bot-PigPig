"""Remembers the last day each story channel moved on, for the daily "previously on…" recap."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Optional, Union

_SCHEMA = """
CREATE TABLE IF NOT EXISTS story_activity (
    channel_id INTEGER PRIMARY KEY,
    last_active_day TEXT NOT NULL
);
"""


class RecapStore:
    def __init__(self, path: Union[str, Path]) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        with self._lock:
            self._connection.executescript(_SCHEMA)
            self._connection.commit()

    def last_active_day(self, channel_id: int) -> Optional[str]:
        with self._lock:
            row = self._connection.execute(
                "SELECT last_active_day FROM story_activity WHERE channel_id = ?", (channel_id,)
            ).fetchone()
        return row[0] if row else None

    def set_active_day(self, channel_id: int, day: str) -> None:
        with self._lock:
            self._connection.execute(
                "INSERT INTO story_activity (channel_id, last_active_day) VALUES (?, ?)"
                " ON CONFLICT (channel_id) DO UPDATE SET last_active_day = excluded.last_active_day",
                (channel_id, day),
            )
            self._connection.commit()
