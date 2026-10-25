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
from typing import Any, Dict, List, Optional, Sequence, Set

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
# Longer "words" are spam (one long run of letters), not something people say.
MAX_WORD_CHARS = 20

# config-table key: first log day (UTC, YYYYMMDD) whose messages were counted live
_LIVE_SINCE_KEY = "stats.live_since"

# How long weekly word/emoji counts and per-message reaction counts are kept
WEEKLY_TERMS_KEEP_DAYS = 84
REACTIONS_KEEP_DAYS = 90


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
        # Reaction changes are written one at a time, in the order the events arrived: a quick
        # add then remove must not run its removal first (it would find nothing to take off).
        self._reaction_lock = asyncio.Lock()

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
    ) -> Optional[Dict[str, Any]]:
        """Insert or update cumulative stats for a single message event.

        Returns:
            The user's updated stats (as ``get_user_stats``) plus ``previous_active_at``,
            the time of their message before this one (None for a first message); None
            when the update failed.
        """
        try:
            return await asyncio.to_thread(
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
            return None

    def _upsert_user_stats_sync(
        self,
        user_id: str,
        guild_id: str,
        message_content: str,
        channel_id: str,
        timestamp: str,
    ) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            previous = _apply_message(conn, user_id, guild_id, message_content, channel_id, timestamp)
            conn.commit()
        stats = self._get_user_stats_sync(user_id, guild_id) or {}
        stats["previous_active_at"] = previous
        return stats

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


    async def get_guild_rankings(
        self, guild_id: str, kind: str, today: Optional[date] = None
    ) -> List[tuple[str, int]]:
        """Ranks a guild's users by all-time messages or by current daily streak.

        Args:
            guild_id: The guild.
            kind: ``"total"`` (all-time messages) or ``"streak"`` (consecutive active days,
                counted only while the streak is alive: active today or yesterday).
            today: The local date (defaults to today).

        Returns:
            ``(user_id, value)`` pairs, highest first; zero values are left out.
        """
        return await asyncio.to_thread(self._get_guild_rankings_sync, guild_id, kind, today or date.today())

    def _get_guild_rankings_sync(self, guild_id: str, kind: str, today: date) -> List[tuple[str, int]]:
        with self.db.get_connection() as conn:
            if kind == "total":
                rows = conn.execute(
                    "SELECT user_id, total_messages AS value FROM user_stats WHERE guild_id = ? AND total_messages > 0 "
                    "ORDER BY total_messages DESC, user_id",
                    (guild_id,),
                ).fetchall()
            elif kind == "streak":
                yesterday = (today - timedelta(days=1)).isoformat()
                rows = conn.execute(
                    "SELECT user_id, streak_days AS value FROM user_stats WHERE guild_id = ? AND streak_days > 0 "
                    "AND streak_last_date >= ? ORDER BY streak_days DESC, user_id",
                    (guild_id, yesterday),
                ).fetchall()
            else:
                raise ValueError(f"Unknown ranking kind: {kind}")
            return [(row["user_id"], row["value"]) for row in rows]

    # ------------------------------------------------------------------
    # channel_weekly_terms / message_reactions
    # ------------------------------------------------------------------

    async def get_weekly_terms(
        self, guild_id: str, week: str, kind: str, limit: int = 10, channel_ids: Optional[Sequence[str]] = None
    ) -> List[tuple[str, int]]:
        """Returns a guild's most used words or emojis in one week.

        Args:
            guild_id: The guild.
            week: The week's Monday as ``YYYY-MM-DD`` (see ``week_start``).
            kind: ``"word"`` or ``"emoji"``.
            limit: How many terms to return.
            channel_ids: Only count these channels (e.g. the public ones); None counts every channel.

        Returns:
            ``(term, count)`` pairs, most used first.
        """
        return await asyncio.to_thread(self._get_weekly_terms_sync, guild_id, week, kind, limit, channel_ids)

    def _get_weekly_terms_sync(
        self, guild_id: str, week: str, kind: str, limit: int, channel_ids: Optional[Sequence[str]]
    ) -> List[tuple[str, int]]:
        if channel_ids is not None and not channel_ids:
            return []
        query = "SELECT term, SUM(count) AS total FROM channel_weekly_terms WHERE guild_id = ? AND week_start = ? AND kind = ?"
        params: List[Any] = [guild_id, week, kind]
        if channel_ids is not None:
            ids = [str(channel_id) for channel_id in channel_ids]
            query += f" AND channel_id IN ({', '.join('?' * len(ids))})"
            params += ids
        query += " GROUP BY term ORDER BY total DESC, term LIMIT ?"
        with self.db.get_connection() as conn:
            rows = conn.execute(query, (*params, limit)).fetchall()
            return [(row["term"], row["total"]) for row in rows]

    async def record_reaction(
        self,
        message_id: str,
        guild_id: str,
        channel_id: str,
        author_id: Optional[str],
        created_at: float,
        delta: int,
        reactor_id: Optional[str] = None,
    ) -> None:
        """Adds or removes one reaction from a message's net reaction count.

        Args:
            message_id: The reacted message.
            guild_id: Its guild.
            channel_id: Its channel.
            author_id: Who wrote it; ``None`` when unknown (a removal), in which case
                only an already counted message is updated.
            created_at: When the message was sent (UNIX time).
            delta: ``1`` for an added reaction, ``-1`` for a removed one.
            reactor_id: Who reacted; a removal by the message's own author is ignored,
                as their reaction was never counted.
        """
        try:
            async with self._reaction_lock:
                await asyncio.to_thread(
                    self._record_reaction_sync, message_id, guild_id, channel_id, author_id, created_at, delta, reactor_id
                )
        except Exception as e:
            await func.report_error(e, f"record_reaction failed (message={message_id})")

    def _record_reaction_sync(
        self,
        message_id: str,
        guild_id: str,
        channel_id: str,
        author_id: Optional[str],
        created_at: float,
        delta: int,
        reactor_id: Optional[str] = None,
    ) -> None:
        with self.db.get_connection() as conn:
            if author_id is None:
                conn.execute(
                    "UPDATE message_reactions SET count = MAX(0, count + ?) WHERE message_id = ? AND author_id != ?",
                    (delta, message_id, reactor_id or ""),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO message_reactions (message_id, guild_id, channel_id, author_id, created_at, count)
                    VALUES (?, ?, ?, ?, ?, MAX(0, ?))
                    ON CONFLICT(message_id) DO UPDATE SET count = MAX(0, count + excluded.count)
                    """,
                    (message_id, guild_id, channel_id, author_id, created_at, delta),
                )
            conn.commit()

    async def get_top_reacted_messages(
        self, guild_id: str, since: float, until: float, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Returns a guild's most reacted messages sent in a time range.

        Args:
            guild_id: The guild.
            since: Range start (UNIX time, inclusive).
            until: Range end (UNIX time, exclusive).
            limit: How many messages to return.

        Returns:
            Rows with ``message_id``, ``channel_id``, ``author_id``, ``created_at`` and
            ``count``, most reacted first; messages without reactions are left out.
        """
        return await asyncio.to_thread(self._get_top_reacted_messages_sync, guild_id, since, until, limit)

    def _get_top_reacted_messages_sync(
        self, guild_id: str, since: float, until: float, limit: int
    ) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT message_id, channel_id, author_id, created_at, count FROM message_reactions "
                "WHERE guild_id = ? AND created_at >= ? AND created_at < ? AND count > 0 "
                "ORDER BY count DESC, created_at LIMIT ?",
                (guild_id, since, until, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    async def reactions_by_author(self, guild_id: str, since: float, until: float) -> List[tuple[str, int]]:
        """Sums the reactions each author's messages sent in a time range received, most first."""
        return await asyncio.to_thread(self._reactions_by_author_sync, guild_id, since, until)

    def _reactions_by_author_sync(self, guild_id: str, since: float, until: float) -> List[tuple[str, int]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT author_id, SUM(count) AS total FROM message_reactions "
                "WHERE guild_id = ? AND created_at >= ? AND created_at < ? AND count > 0 AND author_id IS NOT NULL "
                "GROUP BY author_id ORDER BY total DESC, author_id",
                (guild_id, since, until),
            ).fetchall()
            return [(row["author_id"], row["total"]) for row in rows]

    async def get_regulars(self, guild_id: str, min_messages: int) -> List[Dict[str, Any]]:
        """Returns users with at least ``min_messages`` messages, with ``user_id``, ``total_messages``
        and ``last_active_at``, most messages first."""
        return await asyncio.to_thread(self._get_regulars_sync, guild_id, min_messages)

    def _get_regulars_sync(self, guild_id: str, min_messages: int) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT user_id, total_messages, last_active_at FROM user_stats "
                "WHERE guild_id = ? AND total_messages >= ? ORDER BY total_messages DESC, user_id",
                (guild_id, min_messages),
            ).fetchall()
            return [dict(row) for row in rows]

    async def prune_activity_history(self, now: Optional[datetime] = None) -> None:
        """Deletes weekly term counts and reaction counts that are too old to be shown.

        Args:
            now: The current time (defaults to now).
        """
        try:
            await asyncio.to_thread(self._prune_activity_history_sync, now or datetime.now().astimezone())
        except Exception as e:
            await func.report_error(e, "prune_activity_history failed")

    def _prune_activity_history_sync(self, now: datetime) -> None:
        oldest_week = (now - timedelta(days=WEEKLY_TERMS_KEEP_DAYS)).strftime("%Y-%m-%d")
        oldest_reaction = now.timestamp() - REACTIONS_KEEP_DAYS * 86400
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM channel_weekly_terms WHERE week_start < ?", (oldest_week,))
            conn.execute("DELETE FROM message_reactions WHERE created_at < ?", (oldest_reaction,))
            conn.commit()


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


def week_start(moment: datetime) -> str:
    """Returns the Monday of the week containing ``moment`` (its own date), as ``YYYY-MM-DD``.

    Args:
        moment: A datetime, already in the time zone the week is counted in.

    Returns:
        The week's key in ``channel_weekly_terms``.
    """
    return (moment.date() - timedelta(days=moment.weekday())).isoformat()


def _add_weekly_terms(
    conn: sqlite3.Connection, guild_id: str, channel_id: str, week: str, emojis: List[str], words: List[str]
) -> None:
    """Adds one message's emojis and words to its channel's counts for the week (without committing).

    Args:
        conn: Open connection to the procedural database.
        guild_id: Guild the message was sent in.
        channel_id: Channel the message was sent in.
        week: The week's key (see ``week_start``).
        emojis: Emojis in the message.
        words: Segmented words in the message.
    """
    counts = [("emoji", term, n) for term, n in Counter(emojis).items()]
    counts += [("word", term, n) for term, n in Counter(words).items()]
    if not counts:
        return
    conn.executemany(
        """
        INSERT INTO channel_weekly_terms (guild_id, channel_id, week_start, kind, term, count) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, week_start, kind, term, channel_id) DO UPDATE SET count = count + excluded.count
        """,
        [(guild_id, str(channel_id), week, kind, term, n) for kind, term, n in counts],
    )


def _apply_message(
    conn: sqlite3.Connection,
    user_id: str,
    guild_id: str,
    message_content: str,
    channel_id: str,
    timestamp: str,
) -> Optional[str]:
    """Adds one message to a user's cumulative stats row (without committing).

    Args:
        conn: Open connection to the procedural database.
        user_id: Author's Discord ID.
        guild_id: Guild the message was sent in.
        message_content: Message text.
        channel_id: Channel the message was sent in.
        timestamp: ISO-8601 send time.

    Returns:
        The user's ``last_active_at`` before this message (None for their first one).
    """
    local_time = _local_time(timestamp)
    hour_key = str(local_time.hour)
    today_str = local_time.strftime("%Y-%m-%d")
    emojis = _extract_emojis(message_content)
    words = _segment_words(message_content)
    _add_weekly_terms(conn, guild_id, channel_id, week_start(local_time), emojis, words)

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
        return None

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
    return row.get("last_active_at")


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

    Returns a list of meaningful words (2 to ``MAX_WORD_CHARS`` characters,
    not pure digits, not in the stop-word set).
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
        if len(w) < 2 or len(w) > MAX_WORD_CHARS:
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
