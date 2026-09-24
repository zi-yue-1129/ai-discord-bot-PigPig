# File: `llm/memory/knowledge.py`

## Overview
KnowledgeMemoryProvider: provides guild and channel level knowledge with caching.

## Classes

### `KnowledgeMemory`
Represents the fetched knowledge for a specific context.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(guild_knowledge: Optional[str], channel_knowledge: Optional[str]) -> Any`: No description provided.

### `KnowledgeMemoryProvider`
Provides guild/channel knowledge with caching.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(storage: KnowledgeStorage, max_cache_size: int) -> None`: Initialize with storage and cache limit.
  - `get(guild_id: Optional[str], channel_id: str) -> KnowledgeMemory`: Fetch knowledge for the current guild and channel.
  - `_get_single(target_type: str, target_id: str) -> Optional[str]`: Internal helper with TTL cache and thundering herd protection.
  - `invalidate(target_type: str, target_id: str) -> None`: Invalidate cache for a specific target.

## Functions

No module-level functions defined in this file.

