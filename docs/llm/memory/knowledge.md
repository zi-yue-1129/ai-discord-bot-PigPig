# File: `llm/memory/knowledge.py`

## Overview
KnowledgeMemoryProvider: provides guild and channel level knowledge with caching.

This provider handles retrieval of shared interaction knowledge (memes, facts, etc.)
and implements a TTL cache to optimize performance during message orchestration.

## Classes

### `KnowledgeMemory`
Represents the fetched knowledge for a specific context.

- **Attributes**:
  - `guild_knowledge` (`Any`): Instance attribute for guild_knowledge.
  - `channel_knowledge` (`Any`): Instance attribute for channel_knowledge.

- **Methods**:
  - `__init__(guild_knowledge, channel_knowledge) -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.

### `KnowledgeMemoryProvider`
Provides guild/channel knowledge with caching.

- **Attributes**:
  - `storage` (`Any`): Instance attribute for storage.
  - `max_cache_size` (`Any`): Instance attribute for max_cache_size.
  - `_cache` (`Dict[...]`): Instance attribute for _cache.
  - `_pending_queries` (`Dict[...]`): Instance attribute for _pending_queries.

- **Methods**:
  - `__init__(storage, max_cache_size) -> None`: Initialize with storage and cache limit.
  - `get(guild_id, channel_id) -> KnowledgeMemory`: Fetch knowledge for the current guild and channel.
  - `_get_single(target_type, target_id) -> Optional[...]`: Internal helper with TTL cache and thundering herd protection.
  - `invalidate(target_type, target_id) -> None`: Invalidate cache for a specific target.
