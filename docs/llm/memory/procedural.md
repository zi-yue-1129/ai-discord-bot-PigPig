# File: `llm/memory/procedural.py`

## Overview
Core file handling responsibilities within the `llm/memory` subsystem.

## Classes

### `ProceduralMemoryProvider`
Provides procedural memory for multiple users with per-user TTL cache.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(user_manager: SQLiteUserManager, max_cache_size: int) -> None`: Initializes the provider with a user manager instance and cache size limit.
  - `get(user_ids: List[str]) -> ProceduralMemory`: Fetch procedural memory with per-user TTL cache.
  - `invalidate(user_id: str) -> None`: Evict a single user from the cache.

## Functions

No module-level functions defined in this file.

