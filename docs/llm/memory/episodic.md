# File: `llm/memory/episodic.py`

## Overview
Automatic Episodic Memory Provider for context injection.

Performs a lightweight vector search on each incoming message and returns
the top-k relevant past memory fragments as a formatted string.
Silent failure design: any error returns None without raising.

## Classes

### `EpisodicMemoryProvider`
Retrieve semantically relevant past memory fragments for context injection.

The result is injected into procedural_context_str so both info_agent and
message_agent receive the episodic background without extra tool calls.

Args:
    bot: Discord bot instance (must have vector_manager attribute).
    top_k: Maximum number of fragments to retrieve. Default 3.
    max_chars: Hard character limit for the returned string. Default 1500.
    max_cache_size: Maximum number of entries to retain in the cache. Default 1000.
    cache_ttl: Cache Time-To-Live in seconds. Default 300.0.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `top_k` (`Any`): Instance attribute for top_k.
  - `max_chars` (`Any`): Instance attribute for max_chars.
  - `max_cache_size` (`Any`): Instance attribute for max_cache_size.
  - `cache_ttl` (`Any`): Instance attribute for cache_ttl.
  - `_cache` (`Dict[...]`): Instance attribute for _cache.
  - `_pending_queries` (`Dict[...]`): Instance attribute for _pending_queries.

- **Methods**:
  - `__init__(bot, top_k, max_chars, max_cache_size, cache_ttl) -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `ValueError`.
  - `invalidate(channel_id) -> None`: Invalidate all cached episodic queries for a specific channel.
  - `get(message) -> Optional[...]`: Return formatted episodic context string, or None if nothing relevant.
