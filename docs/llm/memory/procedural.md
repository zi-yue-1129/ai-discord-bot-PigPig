# File: `llm/memory/procedural.py`

## Overview
The `ProceduralMemoryProvider` manages user-specific behavioral data. Unlike Episodic memory (which is about *what happened*), Procedural memory is about *who the user is* and *how the bot should interact with them*.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `procedural.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `ProceduralMemoryProvider`
Provides procedural memory for multiple users with per-user TTL cache.

The provider fetches UserInfo for each user_id using the provided user manager
and caches results per user_id to avoid redundant DB calls within the TTL window.

- **Attributes**:
  - `user_manager` (`Any`): Internal instance state.
  - `max_cache_size` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(user_manager: SQLiteUserManager, max_cache_size: int) -> None`: Initializes the provider with a user manager instance and cache size limit.
  - `get(user_ids: List[str]) -> ProceduralMemory`: Fetch procedural memory with per-user TTL cache.
  - `invalidate(user_id: str) -> None`: Evict a single user from the cache.
