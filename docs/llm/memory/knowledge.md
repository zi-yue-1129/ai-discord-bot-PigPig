# File: `llm/memory/knowledge.py`

## Overview
KnowledgeMemoryProvider: provides guild and channel level knowledge with caching.

This provider handles retrieval of shared interaction knowledge (memes, facts, etc.)
and implements a TTL cache to optimize performance during message orchestration.

## Classes

### `KnowledgeMemory`
Represents the fetched knowledge for a specific context.

- **Attributes**:
  - `guild_knowledge` (`Any`): Instance attribute managing guild_knowledge.
  - `channel_knowledge` (`Any`): Instance attribute managing channel_knowledge.

### `KnowledgeMemoryProvider`
Provides guild/channel knowledge with caching.

- **Attributes**:
  - `storage` (`Any`): Instance attribute managing storage.
  - `max_cache_size` (`Any`): Instance attribute managing max_cache_size.

- **Methods**:
  - `get(guild_id, channel_id) -> KnowledgeMemory`: Fetch knowledge for the current guild and channel.  Args:     guild_id: Discord guild ID.     channel_id: Discord channel ID.      Returns:     KnowledgeMemory object containing both levels of knowledge.
  - `invalidate(target_type, target_id) -> None`: Invalidate cache for a specific target.

