"""Automatic Episodic Memory Provider for context injection.

Performs a lightweight vector search on each incoming message and returns
the top-k relevant past memory fragments as a formatted string.
Silent failure design: any error returns None without raising.
"""
from __future__ import annotations

import asyncio
import re
import time
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

import discord

from addons.logging import get_logger
from function import func
from llm.memory.fragment_time import source_label
from llm.memory.privacy import fragment_user_ids, hidden_in_guild_async, without_hidden_participants
from llm.memory.recent_recall import RecalledFragment, RecentRecall

_LOGGER = get_logger(server_id="Bot", source="llm.memory.episodic")

# Messages shorter than this many tokens (after stripping mentions) are skipped
# to avoid meaningless vector searches on greetings like "hi" or "早安".
_MIN_QUERY_TOKENS = 4

# Fragments scoring below this cosine similarity are not injected. Measured on the
# live collection (qwen3-embedding-4b): noise queries ("哈哈哈哈", "asdf qwer zxcv",
# arithmetic) peak at 0.63-0.65, while questions about real past topics hit 0.69-0.79.
_MIN_RELEVANCE_SCORE = 0.68

# No participants: the result names nobody who could opt out
_NOBODY: FrozenSet[int] = frozenset()

# Pattern to strip Discord mention tags from message content
_MENTION_RE = re.compile(r"<@!?\d+>")

# CJK ideographs, kana and hangul: these scripts do not separate words with spaces
_CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff]")


def _format_entry(label: str, content: str, metadata: Any) -> str:
    """One injected memory line: the summary and its source label, which the bot copies when it uses it.

    The label carries the time as a Discord timestamp. No date is written out as text: the bot copies
    what it sees, and its prompt wants Discord timestamps.

    Args:
        label: The line's tag, such as ``memory #1``.
        content: The fragment's summary.
        metadata: The fragment's metadata.

    Returns:
        The formatted line.
    """
    source = source_label(metadata)
    return f"[{label}] {content}{' ' + source if source else ''}"


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
        recent_ttl: Seconds a recalled fragment is still told to the channel's next messages. Default 600.0.
        recent_max: Recalled fragments kept per channel. Default 5.
    """

    def __init__(
        self,
        bot: Any,
        top_k: int = 3,
        max_chars: int = 1500,
        max_cache_size: int = 1000,
        cache_ttl: float = 300.0,
        recent_ttl: float = 600.0,
        recent_max: int = 5,
    ) -> None:
        if max_cache_size < 0:
            raise ValueError("max_cache_size must be >= 0")
        self.bot = bot
        self.top_k = top_k
        self.max_chars = max_chars
        self.max_cache_size = max_cache_size
        self.cache_ttl = cache_ttl
        # key: (channel_id: str, query: str), value: (formatted_str: Optional[str], expire_at: float monotonic,
        # ids of the people in the fragments formatted_str retells: checked again when the entry is served,
        # the fragments it retells: served again, they are recalled again)
        self._cache: Dict[Tuple[str, str], Tuple[Optional[str], float, FrozenSet[int], Tuple[Any, ...]]] = {}
        # prevents cache stampedes
        self._pending_queries: Dict[Tuple[str, str], asyncio.Event] = {}
        # What was recalled lately in each channel, for the follow-up messages that search finds nothing for
        self.recent = RecentRecall(ttl=recent_ttl, max_per_channel=recent_max)
        # Bumped by every invalidation of a channel: a request that started before it tells nothing from before
        self._generation: Dict[str, int] = {}
        # Bumped when a member's memory is deleted, which concerns every channel
        self._epoch = 0

    def generation(self, channel_id: str) -> int:
        """A number that changes whenever ``channel_id`` is invalidated; read it before a search starts.

        Args:
            channel_id: The Discord channel ID.

        Returns:
            The channel's current generation.
        """
        return self._generation.get(channel_id, 0) + self._epoch

    def forget_user(self, user_id: int) -> None:
        """Forget everything recalled or cached of a member whose memory was deleted.

        Searches in flight are voided as for an invalidation of every channel.

        Args:
            user_id: The member's Discord id.
        """
        self._epoch += 1
        self.recent.forget_user(user_id)
        for key in [key for key, entry in self._cache.items() if user_id in entry[2]]:
            self._cache.pop(key, None)
        for key in list(self._pending_queries):
            event = self._pending_queries.pop(key, None)
            if event:
                event.set()

    def remember(self, channel_id: str, fragments: Any, generation: Optional[int] = None) -> None:
        """Keep fragments the search tool found, so the next messages of the channel still get them.

        Args:
            channel_id: The channel the tool ran in.
            fragments: Memory fragments the tool returned (hidden members' ones already left out).
            generation: The channel's ``generation()`` from before the search started. When the channel
                was invalidated since, the fragments may be outdated and are not kept.
        """
        if generation is not None and generation != self.generation(channel_id):
            return
        self.recent.remember(channel_id, fragments)

    async def invalidate(self, channel_id: str) -> None:
        """Invalidate all cached episodic queries for a specific channel.

        In-flight results are also discarded. Their callers receive None, while
        waiting callers may start a fresh search after invalidation. What was recalled lately in
        the channel is forgotten too.

        Args:
            channel_id: The Discord channel ID.
        """
        self._generation[channel_id] = self._generation.get(channel_id, 0) + 1
        self.recent.forget_channel(channel_id)
        keys_to_remove = [k for k in self._cache.keys() if k[0] == channel_id]
        for k in keys_to_remove:
            self._cache.pop(k, None)

        # Unblock any pending queries that were waiting on a now-invalidated result
        pending_to_remove = [k for k in self._pending_queries.keys() if k[0] == channel_id]
        for k in pending_to_remove:
            event = self._pending_queries.pop(k, None)
            if event:
                event.set()

    async def _read_hidden(self, guild: Any) -> Optional[Set[int]]:
        """The members of ``guild`` who hid themselves (``/leaderboard optout``); nobody in a DM.

        None when the list cannot be read. It is read on a worker thread, so every caller must make its
        cache and ownership decisions after this await, never across it.
        """
        if guild is None:
            return set()
        return await hidden_in_guild_async(self.bot, guild.id)

    def _lookup(self, cache_key: Tuple[str, str], hidden: Set[int]) -> Optional[Tuple[Optional[str], Tuple[Any, ...], FrozenSet[int]]]:
        """The usable cached result for ``cache_key`` as ``(text, fragments told, people in them)``, or None when there is none.

        Synchronous on purpose (no await between reading the entry and using it, so an invalidation
        cannot slip in). A result is checked against the opt-out list each time it is served: someone in
        it may have hidden themselves since; then the entry is dropped and the search runs again.
        """
        entry = self._cache.get(cache_key)
        if entry is None or entry[1] <= time.monotonic():
            return None
        text, _expire_at, participants, told = entry
        if hidden & participants:
            self._cache.pop(cache_key, None)
            return None
        return (text, told, participants)

    async def get(self, message: discord.Message) -> Optional[str]:
        """Return the episodic context for a message: what it matches now plus what was recalled lately.

        Runs in parallel with ProceduralMemoryProvider via asyncio.gather in
        ContextManager, so it does not add serial latency to the pipeline.

        Args:
            message: Current Discord message (provides query text and channel scope).

        Returns:
            Formatted string with past memory fragments, or None.
        """
        # What was recalled before this message: taken now, before any await, so what this message's own
        # search (or a concurrent one) recalls is not told twice and an invalidated search stays discarded.
        channel_id = str(message.channel.id)
        generation = self.generation(channel_id)
        earlier = self.recent.recall(channel_id, set())
        fresh, fresh_people = await self._search(message)
        if not earlier:
            return fresh

        # The last read of the opt-out list decides for everything told, the new search included.
        hidden = await self._read_hidden(getattr(message, "guild", None))
        if hidden is None or self.generation(channel_id) != generation:
            return None  # the list cannot be read, or the channel was invalidated while this request ran
        self.recent.recall(channel_id, hidden)  # forgets the ones of members who hid themselves
        earlier = [fragment for fragment in earlier if self.recent.is_alive(fragment)]  # expired during the search
        if fresh_people & hidden:
            fresh = None
        recent = self._recent_block(earlier, hidden, fresh)
        if recent is None:
            return fresh
        return recent if fresh is None else f"{fresh}\n{recent}"

    def _recent_block(self, earlier: List[RecalledFragment], hidden: Set[int], fresh: Optional[str]) -> Optional[str]:
        """The fragments recalled before this message that ``fresh`` does not already tell.

        Args:
            earlier: The channel's recalled fragments as they were when the message arrived, newest first.
            hidden: The members who hid themselves; their fragments are left out.
            fresh: The block the message's own search produced, or None.

        Returns:
            A formatted block within ``max_chars``, or None when nothing usable is left.
        """
        # Both blocks together stay within max_chars: this one gets what the fresh block left, and its own
        # header and footer count (the fresh block's footer is already in its text).
        budget = self.max_chars - (len(fresh) + 1 if fresh else 0)
        lines = ["--- Recently Recalled Memories ---"]
        footer = "--- End Recently Recalled Memories ---"
        total_chars = len(lines[0]) + len(footer) + 1
        for number, fragment in enumerate([f for f in earlier if not f.participants & hidden], 1):
            if fresh is not None and fragment.content in fresh:
                continue
            entry = _format_entry(f"recalled #{number}", fragment.content, fragment.metadata)
            if total_chars + len(entry) + 1 > budget:
                continue  # too long for what is left; a shorter one behind it may still fit
            lines.append(entry)
            total_chars += len(entry) + 1
        if len(lines) == 1:
            return None
        lines.append(footer)
        return "\n".join(lines)

    async def _search(self, message: discord.Message) -> Tuple[Optional[str], FrozenSet[int]]:
        """Search the vector store for the message and format what is relevant (cached by query).

        Args:
            message: Current Discord message (provides query text and channel scope).

        Returns:
            The formatted string with past memory fragments (or None) and the Discord ids of the
            people in those fragments, for the final opt-out check.
        """
        vector_manager = getattr(self.bot, "vector_manager", None)
        if not vector_manager or not hasattr(vector_manager, "store"):
            return None, _NOBODY

        # Clean query: strip mentions and whitespace
        raw = getattr(message, "content", "") or ""
        query = _MENTION_RE.sub("", raw).strip()

        # Skip trivially short messages (greetings, reactions, single words)
        if _query_tokens(query) < _MIN_QUERY_TOKENS:
            return None, _NOBODY

        channel_id = str(message.channel.id)
        cache_key = (channel_id, query)

        guild = getattr(message, "guild", None)

        # Without the opt-out list nothing is injected, cached or not.
        hidden = await self._read_hidden(guild)
        if hidden is None:
            return None, _NOBODY

        # Thundering herd protection logic. From the lookup to taking ownership below there is no await,
        # so two requests cannot both decide to search, and an invalidation cannot slip in between.
        while True:
            cached = self._lookup(cache_key, hidden)
            if cached is not None:
                self.recent.remember(channel_id, cached[1])  # told again: recalled again
                return cached[0], cached[2]
            if cache_key not in self._pending_queries:
                break
            await self._pending_queries[cache_key].wait()
            # If wait finished but cache wasn't updated (e.g. error in primary task),
            # loop again in case another task picked up the query.
            hidden = await self._read_hidden(guild)
            if hidden is None:
                return None, _NOBODY

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
                return None, _NOBODY

            # What a hidden member (/leaderboard optout) said is not retold, whoever asks; the cached
            # result is already filtered. The list is read again here: someone may have opted out during
            # the search. Without it nothing is injected (and nothing cached).
            hidden = await self._read_hidden(guild) if fragments else set()

            # The event is this search's ownership token. Invalidation removes
            # it, and a newer search may already own the same key. Never return
            # or cache a result from the invalidated generation. Checked after
            # the last await, so nothing can invalidate between check and use.
            if self._pending_queries.get(cache_key) is not event:
                return None, _NOBODY
            if hidden is None:
                return None, _NOBODY
            fragments = without_hidden_participants(fragments, hidden)

            injected: list = []
            if not fragments:
                formatted_result = None
            else:
                lines = ["--- Relevant Past Memories ---"]
                total_chars = len(lines[0])

                for i, frag in enumerate(fragments, 1):
                    entry_str = _format_entry(f"memory #{i}", frag.content, frag.metadata)

                    if total_chars + len(entry_str) + 1 > self.max_chars:
                        break
                    lines.append(entry_str)
                    total_chars += len(entry_str) + 1
                    injected.append(frag)

                lines.append("--- End Past Memories ---")
                _LOGGER.debug(f"Injecting {len(lines) - 2} episodic fragments into context.")
                formatted_result = "\n".join(lines)
                self.recent.remember(channel_id, injected)

            # Update cache
            expire_at = now + self.cache_ttl
            participants = frozenset().union(*(fragment_user_ids(frag.metadata) for frag in fragments))
            self._cache[cache_key] = (formatted_result, expire_at, participants, tuple(injected))

            # Prune expired items if cache is getting large
            if len(self._cache) > self.max_cache_size:
                now_insert = time.monotonic()
                self._cache = {k: v for k, v in self._cache.items() if v[1] > now_insert}

                # If still over size, remove oldest via insertion order
                while len(self._cache) > self.max_cache_size:
                    oldest_key = next(iter(self._cache))
                    self._cache.pop(oldest_key, None)

            return formatted_result, participants
        finally:
            # Always ensure the event is cleaned up and waiting tasks are notified
            # without removing a replacement search after invalidation, including
            # when this search fails or is cancelled.
            if self._pending_queries.get(cache_key) is event:
                self._pending_queries.pop(cache_key, None)
            event.set()
