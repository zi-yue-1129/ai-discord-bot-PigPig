# File: `llm/memory/knowledge.py`

## Overview
KnowledgeMemoryProvider: provides guild and channel level knowledge with caching.

This provider handles retrieval of shared interaction knowledge (memes, facts, etc.)
and implements a TTL cache to optimize performance during message orchestration.

## Classes

### `KnowledgeMemory`
Represents the fetched knowledge for a specific context.

- **Attributes**:
  - `guild_knowledge` (`Any`): Instance attribute guild_knowledge
  - `channel_knowledge` (`Any`): Instance attribute channel_knowledge

- **Methods**:
  - None

### `KnowledgeMemoryProvider`
Provides guild/channel knowledge with caching.

- **Attributes**:
  - `storage` (`Any`): Instance attribute storage
  - `max_cache_size` (`Any`): Instance attribute max_cache_size
  - `_cache` (`Dict[Tuple[str, str], Tuple[Optional[str], float]]`): Instance attribute _cache
  - `_pending_queries` (`Dict[Tuple[str, str], asyncio.Event]`): Instance attribute _pending_queries

- **Methods**:
  - `get(self, guild_id, channel_id) -> KnowledgeMemory`: Fetch knowledge for the current guild and channel.  Args:     guild_id: Discord guild ID.     channel_id: Discord channel ID.      Returns:     KnowledgeMemory object containing both levels of knowledge.
  - `_get_single(self, target_type, target_id) -> Optional[str]`: Internal helper with TTL cache and thundering herd protection.
  - `invalidate(self, target_type, target_id) -> None`: Invalidate cache for a specific target.

## Functions

None

