# File: `llm/memory/procedural.py`

## Overview
This file is part of the llm subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `ProceduralMemoryProvider`
Provides procedural memory for multiple users with per-user TTL cache.

The provider fetches UserInfo for each user_id using the provided user manager
and caches results per user_id to avoid redundant DB calls within the TTL window.

- **Attributes**:
  - `user_manager` (`Any`): Attribute holding user_manager data.
  - `max_cache_size` (`Any`): Attribute holding max_cache_size data.
  - `_cache` (`Dict[Tuple[str, Tuple[Tuple[Optional[UserInfo], float]]]]`): Attribute holding _cache data.
  - `_pending_queries` (`Dict[Tuple[str, asyncio.Event]]`): Attribute holding _pending_queries data.

- **Methods**:
  - `__init__(user_manager: SQLiteUserManager, max_cache_size: int) -> None`: Initializes the provider with a user manager instance and cache size limit.
  - `get(user_ids: List[str]) -> ProceduralMemory`: Fetch procedural memory with per-user TTL cache.
  - `invalidate(user_id: str) -> None`: Evict a single user from the cache.

## Functions

No top-level functions defined.
