# File: `llm/memory/procedural.py`

## Overview
This file is part of the LLM integration and orchestration pipeline and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `llm/memory/procedural.py`.

## Classes

### `ProceduralMemoryProvider`
Provides procedural memory for multiple users with per-user TTL cache.  The provider fetches UserInfo for each user_id using the provided user manager and caches results per user_id to avoid redundant DB calls within the TTL window.

- **Attributes**:
  - `user_manager` (`Any`): Instance attribute user_manager
  - `max_cache_size` (`Any`): Instance attribute max_cache_size
  - `_cache` (`Dict[str, Tuple[Optional[UserInfo], float]]`): Instance attribute _cache
  - `_pending_queries` (`Dict[str, asyncio.Event]`): Instance attribute _pending_queries

- **Methods**:
  - `get(self, user_ids) -> ProceduralMemory`: Fetch procedural memory with per-user TTL cache.  Cache hit: return cached UserInfo without DB call. Cache miss: fetch from DB and store in cache.  Args:     user_ids: List of user id strings to fetch info for.  Returns:     ProceduralMemory containing a dict mapping user_id to UserInfo.
  - `invalidate(self, user_id) -> None`: Evict a single user from the cache.  Call this after a successful /memory save to ensure the next request reflects the updated data without waiting for TTL expiry.  Args:     user_id: The user_id string to remove from cache.

## Functions

None

