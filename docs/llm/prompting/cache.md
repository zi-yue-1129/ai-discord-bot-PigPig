# File: `llm/prompting/cache.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `cache` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `PromptCache`
Intelligent caching system for prompt components and combinations.

- **Attributes**:
  - `cache_storage` (`Dict[...]`): Instance attribute for cache_storage.
  - `ttl_storage` (`Dict[...]`): Instance attribute for ttl_storage.
  - `precompiled_cache` (`Dict[...]`): Instance attribute for precompiled_cache.
  - `access_count` (`Dict[...]`): Instance attribute for access_count.
  - `_lock` (`Any`): Instance attribute for _lock.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__() -> Any`: Initialize the cache storage and monitoring structures.
  - `get(key) -> Optional[...]`: Retrieve a cached item if it exists and has not expired.
  - `set(key, value, ttl) -> None`: Set a value in the cache with a specific time-to-live.
  - `invalidate(key) -> None`: Explicitly remove an item from the cache.
  - `clear_all() -> None`: Clear all cached items and metadata.
  - `is_expired(key) -> bool`: Check if a cached item has passed its expiration time.
  - `precompile_templates(config) -> None`: Precompile common prompt module combinations to reduce runtime overhead.
  - `get_precompiled(key) -> Optional[...]`: Retrieve a precompiled template combination.
  - `cleanup_expired() -> int`: Iterate through the cache and remove all expired items.
  - `get_cache_stats() -> Dict[...]`: Retrieve usage and performance statistics for the cache.
  - `get_cache_keys(prefix) -> Set[...]`: Retrieve all keys currently in the cache.
  - `extend_ttl(key, additional_seconds) -> bool`: Extend the life of a cached item by adding more time to its expiration.
