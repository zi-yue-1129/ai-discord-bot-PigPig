# File: `llm/memory/procedural.py`

## Overview
The `ProceduralMemoryProvider` manages user-specific behavioral data. Unlike Episodic memory (which is about *what happened*), Procedural memory is about *who the user is* and *how the bot should interact with them*.

## Classes

### `ProceduralMemoryProvider`
Provides procedural memory for multiple users with per-user TTL cache.

The provider fetches UserInfo for each user_id using the provided user manager
and caches results per user_id to avoid redundant DB calls within the TTL window.

- **Attributes**:
  - `user_manager` (`Any`): Instance attribute managing user_manager.
  - `max_cache_size` (`Any`): Instance attribute managing max_cache_size.

- **Methods**:
  - `get(user_ids) -> ProceduralMemory`: Fetch procedural memory with per-user TTL cache.  Cache hit: return cached UserInfo without DB call. Cache miss: fetch from DB and store in cache.  Args:     user_ids: List of user id strings to fetch info for.  Returns:     ProceduralMemory containing a dict mapping user_id to UserInfo.
  - `invalidate(user_id) -> None`: Evict a single user from the cache.  Call this after a successful /memory save to ensure the next request reflects the updated data without waiting for TTL expiry.  Args:     user_id: The user_id string to remove from cache.

