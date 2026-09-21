# File: `llm/memory/knowledge.py`

## Overview
KnowledgeMemoryProvider: provides guild and channel level knowledge with caching.

This provider handles retrieval of shared interaction knowledge (memes, facts, etc.)
and implements a TTL cache to optimize performance during message orchestration.

## Classes

### `KnowledgeMemory`
Represents the fetched knowledge for a specific context.

- **Attributes**:
  - `guild_knowledge` (`Any`): Attribute holding guild_knowledge data.
  - `channel_knowledge` (`Any`): Attribute holding channel_knowledge data.

- **Methods**:
  - `__init__(guild_knowledge: Optional[str], channel_knowledge: Optional[str]) -> Any`: Executes __init__ logic.

### `KnowledgeMemoryProvider`
Provides guild/channel knowledge with caching.

- **Attributes**:
  - `storage` (`Any`): Attribute holding storage data.
  - `max_cache_size` (`Any`): Attribute holding max_cache_size data.
  - `_cache` (`Dict[Tuple[Tuple[Tuple[str, str]], Tuple[Tuple[Optional[str], float]]]]`): Attribute holding _cache data.
  - `_pending_queries` (`Dict[Tuple[Tuple[Tuple[str, str]], asyncio.Event]]`): Attribute holding _pending_queries data.

- **Methods**:
  - `__init__(storage: KnowledgeStorage, max_cache_size: int) -> None`: Initialize with storage and cache limit.
  - `get(guild_id: Optional[str], channel_id: str) -> KnowledgeMemory`: Fetch knowledge for the current guild and channel.
  - `_get_single(target_type: str, target_id: str) -> Optional[str]`: Internal helper with TTL cache and thundering herd protection.
  - `invalidate(target_type: str, target_id: str) -> None`: Invalidate cache for a specific target.

## Functions

No top-level functions defined.
