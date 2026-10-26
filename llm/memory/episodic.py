"""Automatic Episodic Memory Provider for context injection.

Performs a lightweight vector search on each incoming message and returns
the top-k relevant past memory fragments as a formatted string.
Silent failure design: any error returns None without raising.
"""
from __future__ import annotations

import asyncio
import re
import time
from typing import Any, Dict, FrozenSet, Optional, Tuple

import discord

from addons.logging import get_logger
from function import func
from llm.memory.privacy import fragment_user_ids, hidden_in_guild_async, without_hidden_participants

_LOGGER = get_logger(server_id="Bot", source="llm.memory.episodic")

# Messages shorter than this many tokens (after stripping mentions) are skipped
# to avoid meaningless vector searches on greetings like "hi" or "早安".
_MIN_QUERY_TOKENS = 4

# Fragments scoring below this cosine similarity are not injected. Measured on the
# live collection (qwen3-embedding-4b): noise queries ("哈哈哈哈", "asdf qwer zxcv",
# arithmetic) peak at 0.63-0.65, while questions about real past topics hit 0.69-0.79.
_MIN_RELEVANCE_SCORE = 0.68

# Pattern to strip Discord mention tags from message content
_MENTION_RE = re.compile(r"<@!?\d+>")

# CJK ideographs, kana and hangul: these scripts do not separate words with spaces
_CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff]")


def _query_tokens(query: str) -> int:
    """Counts query tokens: each CJK character plus each space-separated word.

    Args:
        query: Message text without mentions.

    Returns:
        The token count used for the minimum-length check.
    """
    return len(_CJK_RE.findall(query)) + len(_CJK_RE.sub(" ", query).split())


class EpisodicMemoryProvider:
    """Retrieve semantically relevant past memory fragments for context injection.

    The result is injected into procedural_context_str so both info_agent and
    message_agent receive the episodic background without extra tool calls.

    Args:
        bot: Discord bot instance (must have vector_manager attribute).
        top_k: Maximum number of fragments to retrieve. Default 3.
        max_chars: Hard character limit for the returned string. Default 1500.
        max_cache_size: Maximum number of entries to retain in the cache. Default 1000.
        cache_ttl: Cache Time-To-Live in seconds. Default 300.0.
    """

    def __init__(self, bot: Any, top_k: int = 3, max_chars: int = 1500, max_cache_size: int = 1000, cache_ttl: float = 300.0) -> None:
        if max_cache_size < 0:
            raise ValueError("max_cache_size must be >= 0")
        self.bot = bot
        self.top_k = top_k
        self.max_chars = max_chars
        self.max_cache_size = max_cache_size
        self.cache_ttl = cache_ttl
        # key: (channel_id: str, query: str), value: (formatted_str: Optional[str], expire_at: float monotonic,
        # ids of the people in the fragments formatted_str retells: checked again when the entry is served)
        self._cache: Dict[Tuple[str, str], Tuple[Optional[str], float, FrozenSet[int]]] = {}
        # prevents cache stampedes
        self._pending_queries: Dict[Tuple[str, str], asyncio.Event] = {}

    async def invalidate(self, channel_id: str) -> None:
        """Invalidate all cached episodic queries for a specific channel.

        In-flight results are also discarded. Their callers receive None, while
        waiting callers may start a fresh search after invalidation.

        Args:
            channel_id: The Discord channel ID.
        """
        keys_to_remove = [k for k in self._cache.keys() if k[0] == channel_id]
        for k in keys_to_remove:
            self._cache.pop(k, None)

        # Unblock any pending queries that were waiting on a now-invalidated result
        pending_to_remove = [k for k in self._pending_queries.keys() if k[0] == channel_id]
        for k in pending_to_remove:
            event = self._pending_queries.pop(k, None)
            if event:
                event.set()

    async def _cached(self, cache_key: Tuple[str, str], guild: Any) -> Optional[Tuple[Optional[str]]]:
        """The usable cached result for ``cache_key`` as a 1-tuple, or None when there is none.

        A result is checked against the opt-out list each time it is served: someone in it may have hidden
        themselves since (``/leaderboard optout``). Then the entry is dropped and the search runs again;
        while the list cannot be read nothing is served.
        """
        entry = self._cache.get(cache_key)
        if entry is None or entry[1] <= time.monotonic():
            return None
        text, _expire_at, participants = entry
        if guild is not None and participants:
            hidden = await hidden_in_guild_async(self.bot, guild.id)
            if hidden is None:
                return (None,)
            if hidden & participants:
                if self._cache.get(cache_key) is entry:
                    self._cache.pop(cache_key, None)
                return None
        return (text,)

    async def get(self, message: discord.Message) -> Optional[str]:
        """Return formatted episodic context string, or None if nothing relevant.

        Runs in parallel with ProceduralMemoryProvider via asyncio.gather in
        ContextManager, so it does not add serial latency to the pipeline.

        Args:
            message: Current Discord message (provides query text and channel scope).

        Returns:
            Formatted string with past memory fragments, or None.
        """
        vector_manager = getattr(self.bot, "vector_manager", None)
        if not vector_manager or not hasattr(vector_manager, "store"):
            return None

        # Clean query: strip mentions and whitespace
        raw = getattr(message, "content", "") or ""
        query = _MENTION_RE.sub("", raw).strip()

        # Skip trivially short messages (greetings, reactions, single words)
        if _query_tokens(query) < _MIN_QUERY_TOKENS:
            return None

        channel_id = str(message.channel.id)
        cache_key = (channel_id, query)

        guild = getattr(message, "guild", None)

        # Thundering herd protection logic
        while cache_key in self._pending_queries:
            await self._pending_queries[cache_key].wait()
            cached = await self._cached(cache_key, guild)
            if cached is not None:
                return cached[0]
            # If wait finished but cache wasn't updated (e.g. error in primary task),
            # loop again in case another task picked up the query.

        cached = await self._cached(cache_key, guild)
        if cached is not None:
            return cached[0]
        now = time.monotonic()

        event = asyncio.Event()
        self._pending_queries[cache_key] = event

        try:
            try:
                fragments = await vector_manager.store.search_memories_by_vector(
                    query_text=query,
                    limit=self.top_k,
                    channel_id=channel_id,
                    min_score=_MIN_RELEVANCE_SCORE,
                )
            except Exception as e:
                await func.report_error(e, "EpisodicMemoryProvider.get: vector search failed")
                return None

            # The event is this search's ownership token. Invalidation removes
            # it, and a newer search may already own the same key. Never return
            # or cache a result from the invalidated generation.
            if self._pending_queries.get(cache_key) is not event:
                return None

            # What a hidden member (/leaderboard optout) said is not retold, whoever asks; the cached
            # result is already filtered. Without the opt-out list nothing is injected.
            if fragments and guild is not None:
                fragments = without_hidden_participants(fragments, await hidden_in_guild_async(self.bot, guild.id))

            if not fragments:
                formatted_result = None
            else:
                lines = ["--- Relevant Past Memories ---"]
                total_chars = len(lines[0])

                for i, frag in enumerate(fragments, 1):
                    ts = frag.metadata.get("start_timestamp") or frag.metadata.get("timestamp")
                    jump_url = frag.metadata.get("jump_url")

                    # Build source label: prefer a Discord message link over plain timestamp
                    if jump_url and ts:
                        try:
                            unix_ts = int(float(ts))
                            source_str = f" [[Source <t:{unix_ts}:R>]({jump_url})]"
                        except Exception:
                            source_str = f" [[Source]({jump_url})]"
                    elif jump_url:
                        source_str = f" [[Source]({jump_url})]"
                    elif ts:
                        try:
                            unix_ts = int(float(ts))
                            source_str = f" [<t:{unix_ts}:R>]"
                        except Exception:
                            source_str = ""
                    else:
                        source_str = ""

                    entry_str = f"[memory #{i}] {frag.content}{source_str}"

                    if total_chars + len(entry_str) + 1 > self.max_chars:
                        break
                    lines.append(entry_str)
                    total_chars += len(entry_str) + 1

                lines.append("--- End Past Memories ---")
                _LOGGER.debug(f"Injecting {len(lines) - 2} episodic fragments into context.")
                formatted_result = "\n".join(lines)

            # Update cache
            expire_at = now + self.cache_ttl
            participants = frozenset().union(*(fragment_user_ids(frag.metadata) for frag in fragments))
            self._cache[cache_key] = (formatted_result, expire_at, participants)

            # Prune expired items if cache is getting large
            if len(self._cache) > self.max_cache_size:
                now_insert = time.monotonic()
                self._cache = {k: v for k, v in self._cache.items() if v[1] > now_insert}

                # If still over size, remove oldest via insertion order
                while len(self._cache) > self.max_cache_size:
                    oldest_key = next(iter(self._cache))
                    self._cache.pop(oldest_key, None)

            return formatted_result
        finally:
            # Always ensure the event is cleaned up and waiting tasks are notified
            # without removing a replacement search after invalidation, including
            # when this search fails or is cancelled.
            if self._pending_queries.get(cache_key) is event:
                self._pending_queries.pop(cache_key, None)
            event.set()
