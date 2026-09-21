# File: `llm/prompting/cache.py`

## Overview
This file is part of the llm subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `PromptCache`
Intelligent caching system for prompt components and combinations.

- **Attributes**:
  - `cache_storage` (`Dict[Tuple[str, Any]]`): Attribute holding cache_storage data.
  - `ttl_storage` (`Dict[Tuple[str, datetime]]`): Attribute holding ttl_storage data.
  - `precompiled_cache` (`Dict[Tuple[str, str]]`): Attribute holding precompiled_cache data.
  - `access_count` (`Dict[Tuple[str, int]]`): Attribute holding access_count data.
  - `_lock` (`Any`): Attribute holding _lock data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__() -> Any`: Initialize the cache storage and monitoring structures.
  - `get(key: str) -> Optional[Any]`: Retrieve a cached item if it exists and has not expired.
  - `set(key: str, value: Any, ttl: int) -> None`: Set a value in the cache with a specific time-to-live.
  - `invalidate(key: str) -> None`: Explicitly remove an item from the cache.
  - `clear_all() -> None`: Clear all cached items and metadata.
  - `is_expired(key: str) -> bool`: Check if a cached item has passed its expiration time.
  - `precompile_templates(config: dict) -> None`: Precompile common prompt module combinations to reduce runtime overhead.
  - `get_precompiled(key: str) -> Optional[str]`: Retrieve a precompiled template combination.
  - `cleanup_expired() -> int`: Iterate through the cache and remove all expired items.
  - `get_cache_stats() -> Dict[Tuple[str, Any]]`: Retrieve usage and performance statistics for the cache.
  - `get_cache_keys(prefix: str) -> Set[str]`: Retrieve all keys currently in the cache.
  - `extend_ttl(key: str, additional_seconds: int) -> bool`: Extend the life of a cached item by adding more time to its expiration.

## Functions

No top-level functions defined.
