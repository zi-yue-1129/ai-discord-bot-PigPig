"""StatsStorage: handles user statistics and log migration state persistence.

This module provides CRUD operations for the user_stats and
log_migration_state tables, supporting real-time message tracking and
historical log migration.
"""
from __future__ import annotations

import json
import re
import sqlite3
import asyncio
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from .connection import DatabaseConnection
from function import func
from addons.logging import get_logger

logger = get_logger(server_id="system", source=__name__)

# ---------------------------------------------------------------------------
# Chinese / CJK stop-words (compact set for jieba filtering)
# ---------------------------------------------------------------------------
_STOP_WORDS: Set[str] = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一個", "上", "也", "很", "到", "說", "要", "去", "你", "會", "著",
    "沒有", "看", "好", "自己", "這", "他", "她", "它", "麼", "嗎", "吧",
    "啊", "嗯", "喔", "欸", "耶", "呢", "哦", "哈", "噢", "呀", "唉",
    "把", "讓", "被", "從", "而", "且", "但", "跟", "對", "所以", "因為",
    "如果", "那", "還", "比", "這個", "那個", "什麼", "怎麼", "可以",
    "沒", "能", "已經", "過", "之", "等", "多", "時", "個", "可", "來",
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "am",
    "do", "did", "does", "i", "you", "he", "she", "it", "we", "they",
    "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "that", "this", "not", "no", "so", "if", "my", "me", "your",
}

# Regex for extracting emoji (both Unicode and Discord custom <:name:id>)
_UNICODE_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE,
)
_DISCORD_EMOJI_RE = re.compile(r"<a?:\w+:\d+>")

# Maximum number of words to keep in top_words to prevent unbounded growth
_MAX_TOP_WORDS = 200

# config-table key: first log day (UTC, YYYYMMDD) whose messages were counted live
_LIVE_SINCE_KEY = "stats.live_since"


class StatsStorage:
    """Handles user_stats and log_migration_state table operations.

    Attributes:
        db: The shared DatabaseConnection instance.
    """

    def __init__(self, db: DatabaseConnection) -> None:
        """Initialize with a DatabaseConnection instance.

        Args:
            db: The shared SQLite connection manager.
        """
        self.db = db
        self.logger = logger

    # ------------------------------------------------------------------
    # user_stats CRUD
    # ------------------------------------------------------------------

    async def get_user_stats(
        self, user_id: str, guild_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cumulative stats for a user in a guild."""
        try:
            return await asyncio.to_thread(self._get_user_stats_sync, user_id, guild_id)
        except Exception as e:
            await func.report_error(
                e, f"get_user_stats failed (user={user_id}, guild={guild_id})"
            )
            return None

    def _get_user_stats_sync(self, user_id: str, guild_id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM user_stats WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id),
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            res = dict(row)
            # Parse JSON columns
            for col in ["active_hours", "top_channels", "top_emojis", "top_words"]:
                if res.get(col):
                    res[col] = _safe_json_load(res[col])
            return res

    async def upsert_user_stats(
        self,
        user_id: str,
        guild_id: str,
        message_content: str,
        channel_id: str,
        timestamp: str,
    ) -> None:
        """Insert or update cumulative stats for a single message event."""
        try:
            await asyncio.to_thread(
                self._upsert_user_stats_sync,
                user_id,
                guild_id,
                message_content,
                channel_id,
                timestamp,
            )
        except Exception as e:
            await func.report_error(
                e,
                f"upsert_user_stats failed (user={user_id}, guild={guild_id})",
            )

    def _upsert_user_stats_sync(
        self,
        user_id: str,
        guild_id: str,
        message_content: str,
        channel_id: str,
        timestamp: str,
    ) -> None:
        with self.db.get_connection() as conn:
            _apply_message(conn, user_id, guild_id, message_content, channel_id, timestamp)
            conn.commit()

    async def bulk_upsert_user_stats(self, records: List[Dict[str, Any]]) -> None:
        """Insert or update cumulative stats for a batch of message events."""
        if not records:
            return

        try:
            await asyncio.to_thread(self._bulk_upsert_user_stats_sync, records)
        except Exception as e:
            await func.report_error(e, "bulk_upsert_user_stats failed")

    def _bulk_upsert_user_stats_sync(self, records: List[Dict[str, Any]]) -> None:
        with self.db.get_connection() as conn:
            for rec in records:
                _apply_message(
                    conn,
                    rec["user_id"],
                    rec["guild_id"],
                    rec["message_content"],
                    rec["channel_id"],
                    rec["timestamp"],
                )
            conn.commit()

    # ------------------------------------------------------------------
    # log_migration_state CRUD
    # ------------------------------------------------------------------

    async def get_migration_state(self, guild_id: str) -> Optional[str]:
        """Get the last processed date for historical log migration."""
        try:
            return await asyncio.to_thread(self._get_migration_state_sync, guild_id)
        except Exception as e:
            await func.report_error(
                e, f"get_migration_state failed (guild={guild_id})"
            )
            return None

    def _get_migration_state_sync(self, guild_id: str) -> Optional[str]:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT last_processed_date FROM log_migration_state WHERE guild_id = ?",
                (guild_id,),
            )
            row = cursor.fetchone()
            return row["last_processed_date"] if row else None

    async def set_migration_state(self, guild_id: str, date_str: str) -> None:
        """Record the last processed date for historical log migration."""
        try:
            await asyncio.to_thread(self._set_migration_state_sync, guild_id, date_str)
        except Exception as e:
            await func.report_error(
                e, f"set_migration_state failed (guild={guild_id})"
            )

    def _set_migration_state_sync(self, guild_id: str, date_str: str) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO log_migration_state (guild_id, last_processed_date)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    last_processed_date = excluded.last_processed_date
                """,
                (guild_id, date_str),
            )
            conn.commit()

    async def get_or_init_live_since(self, today: str) -> str:
        """Returns the first log day whose messages were already counted live.

        Logs are written by the running bot, which counts every message as it
        arrives, so only days before this marker may be imported from logs. The
        marker is set once: after the earliest recorded import when upgrading
        (every later day was counted live), otherwise today.

        Args:
            today: Today's log-folder date (UTC, ``YYYYMMDD``).

        Returns:
            The marker date (``YYYYMMDD``).
        """
        return await asyncio.to_thread(self._get_or_init_live_since_sync, today)

    def _get_or_init_live_since_sync(self, today: str) -> str:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT value FROM config WHERE key = ?", (_LIVE_SINCE_KEY,)).fetchone()
            if row:
                return row["value"]
            earliest = conn.execute("SELECT MIN(last_processed_date) AS day FROM log_migration_state").fetchone()
            if earliest and earliest["day"]:
                live_since = (datetime.strptime(earliest["day"], "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
            else:
                live_since = today
            conn.execute("INSERT INTO config (key, value) VALUES (?, ?)", (_LIVE_SINCE_KEY, live_since))
            conn.commit()
            return live_since


# ======================================================================
# Helper functions (module-private)
# ======================================================================


def _local_time(timestamp: str) -> datetime:
    """Parses a message timestamp and converts it to the server's local time.

    Discord and the logs give UTC; hours and streak days are shown as local time.

    Args:
        timestamp: ISO-8601 timestamp, possibly ending in ``Z``.

    Returns:
        The aware local datetime (now, when the timestamp cannot be parsed).
    """
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        logger.warning("Unparseable stats timestamp %r; using the current time.", timestamp)
        return datetime.now().astimezone()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone()


def _apply_message(
    conn: sqlite3.Connection,
    user_id: str,
    guild_id: str,
    message_content: str,
    channel_id: str,
    timestamp: str,
) -> None:
    """Adds one message to a user's cumulative stats row (without committing).

    Args:
        conn: Open connection to the procedural database.
        user_id: Author's Discord ID.
        guild_id: Guild the message was sent in.
        message_content: Message text.
        channel_id: Channel the message was sent in.
        timestamp: ISO-8601 send time.
    """
    local_time = _local_time(timestamp)
    hour_key = str(local_time.hour)
    today_str = local_time.strftime("%Y-%m-%d")
    emojis = _extract_emojis(message_content)
    words = _segment_words(message_content)

    existing = conn.execute(
        "SELECT * FROM user_stats WHERE user_id = ? AND guild_id = ?",
        (user_id, guild_id),
    ).fetchone()

    if not existing:
        conn.execute(
            """
            INSERT INTO user_stats (
                user_id, guild_id, total_messages,
                active_hours, top_channels, top_emojis, top_words,
                streak_days, streak_last_date,
                last_active_at, first_message_at
            ) VALUES (?, ?, 1, ?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (
                user_id,
                guild_id,
                json.dumps({hour_key: 1}, ensure_ascii=False),
                json.dumps({channel_id: 1} if channel_id else {}, ensure_ascii=False),
                json.dumps(dict(Counter(emojis)), ensure_ascii=False),
                json.dumps(_add_words({}, words), ensure_ascii=False),
                today_str,
                timestamp,
                timestamp,
            ),
        )
        return

    row = dict(existing)
    active_hours = _safe_json_load(row.get("active_hours", "{}"))
    active_hours[hour_key] = active_hours.get(hour_key, 0) + 1

    top_channels = _safe_json_load(row.get("top_channels", "{}"))
    if channel_id:
        top_channels[channel_id] = top_channels.get(channel_id, 0) + 1

    top_emojis = _safe_json_load(row.get("top_emojis", "{}"))
    for em in emojis:
        top_emojis[em] = top_emojis.get(em, 0) + 1

    top_words = _add_words(_safe_json_load(row.get("top_words", "{}")), words)

    streak_days, streak_last_date = _compute_streak(
        row.get("streak_days", 0), row.get("streak_last_date"), today_str
    )

    conn.execute(
        """
        UPDATE user_stats SET
            total_messages = ?,
            active_hours = ?,
            top_channels = ?,
            top_emojis = ?,
            top_words = ?,
            streak_days = ?,
            streak_last_date = ?,
            last_active_at = ?,
            first_message_at = ?
        WHERE user_id = ? AND guild_id = ?
        """,
        (
            row.get("total_messages", 0) + 1,
            json.dumps(active_hours, ensure_ascii=False),
            json.dumps(top_channels, ensure_ascii=False),
            json.dumps(top_emojis, ensure_ascii=False),
            json.dumps(top_words, ensure_ascii=False),
            streak_days,
            streak_last_date,
            timestamp,
            row.get("first_message_at") or timestamp,
            user_id,
            guild_id,
        ),
    )


def _safe_json_load(raw: Any) -> Dict[str, int]:
    """Safely parse a JSON string into a dict, defaulting to empty dict."""
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _extract_emojis(text: str) -> List[str]:
    """Extract Unicode and Discord custom emojis from text."""
    if not text:
        return []
    results: List[str] = []
    # Unicode emojis
    for match in _UNICODE_EMOJI_RE.finditer(text):
        # Each character in the match is a separate emoji
        for ch in match.group():
            results.append(ch)
    # Discord custom emojis  <:name:id> or <a:name:id>
    for match in _DISCORD_EMOJI_RE.finditer(text):
        results.append(match.group())
    return results


def _segment_words(text: str) -> List[str]:
    """Segment text using jieba and filter stop-words / noise.

    Returns a list of meaningful words (length >= 2, not pure digits,
    not in the stop-word set).
    """
    if not text:
        return []
    try:
        import jieba
    except ImportError:
        logger.warning("jieba not installed; skipping word segmentation.")
        return []

    # Remove URLs, mentions, and custom emoji markup before segmenting
    cleaned = re.sub(r"https?://\S+", "", text)
    cleaned = re.sub(r"<@!?\d+>", "", cleaned)
    cleaned = re.sub(r"<#\d+>", "", cleaned)
    cleaned = re.sub(r"<a?:\w+:\d+>", "", cleaned)

    words: List[str] = []
    for word in jieba.cut(cleaned):
        w = word.strip().lower()
        if len(w) < 2:
            continue
        if w.isdigit():
            continue
        if w in _STOP_WORDS:
            continue
        words.append(w)
    return words


def _add_words(top_words: Dict[str, int], words: List[str]) -> Dict[str, int]:
    """Counts words into a bounded table with the Space-Saving algorithm.

    When the table is full, a new word replaces the least-counted entry and
    inherits its count plus one. Plain top-N trimming would drop every new word
    (count 1) forever once the table filled, freezing the word cloud; with
    Space-Saving any word used often enough is guaranteed to get in.

    Args:
        top_words: Existing word counts (modified and returned).
        words: Words from one message.

    Returns:
        The updated table, at most ``_MAX_TOP_WORDS`` entries.
    """
    while len(top_words) > _MAX_TOP_WORDS:
        del top_words[min(top_words, key=top_words.get)]
    for word in words:
        if word in top_words:
            top_words[word] += 1
        elif len(top_words) < _MAX_TOP_WORDS:
            top_words[word] = 1
        else:
            evicted = min(top_words, key=top_words.get)
            top_words[word] = top_words.pop(evicted) + 1
    return top_words


def _compute_streak(
    current_streak: int, last_date_str: Optional[str], today_str: str
) -> tuple[int, str]:
    """Compute the updated streak days based on the last active date.

    Args:
        current_streak: The current consecutive active days count.
        last_date_str: The last active date in YYYY-MM-DD format, or None.
        today_str: Today's date in YYYY-MM-DD format.

    Returns:
        A tuple of (updated_streak_days, updated_last_date_str).
    """
    if not last_date_str:
        return 1, today_str

    if last_date_str == today_str:
        # Same day, no change
        return current_streak, today_str

    try:
        last_date = date.fromisoformat(last_date_str)
        today = date.fromisoformat(today_str)
        diff = (today - last_date).days

        if diff == 1:
            # Consecutive day
            return current_streak + 1, today_str
        elif diff > 1:
            # Streak broken
            return 1, today_str
        else:
            # Negative diff (shouldn't happen), keep current
            return current_streak, last_date_str
    except (ValueError, TypeError):
        return 1, today_str
