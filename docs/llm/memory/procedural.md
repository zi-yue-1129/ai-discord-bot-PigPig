# File: `llm/memory/procedural.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `procedural` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `ProceduralMemoryProvider`
Provides procedural memory for multiple users with per-user TTL cache.

The provider fetches UserInfo for each user_id using the provided user manager
and caches results per user_id to avoid redundant DB calls within the TTL window.

- **Attributes**:
  - `user_manager` (`Any`): Instance attribute for user_manager.
  - `max_cache_size` (`Any`): Instance attribute for max_cache_size.
  - `_cache` (`Dict[...]`): Instance attribute for _cache.
  - `_pending_queries` (`Dict[...]`): Instance attribute for _pending_queries.

- **Methods**:
  - `__init__(user_manager, max_cache_size) -> None`: Initializes the provider with a user manager instance and cache size limit.
  - `get(user_ids) -> ProceduralMemory`: Fetch procedural memory with per-user TTL cache.
  - `invalidate(user_id) -> None`: Evict a single user from the cache.
