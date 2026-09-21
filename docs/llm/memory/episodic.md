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
  - `bot` (`Any`): Attribute holding bot data.
  - `top_k` (`Any`): Attribute holding top_k data.
  - `max_chars` (`Any`): Attribute holding max_chars data.
  - `max_cache_size` (`Any`): Attribute holding max_cache_size data.
  - `cache_ttl` (`Any`): Attribute holding cache_ttl data.
  - `_cache` (`Dict[Tuple[Tuple[Tuple[str, str]], Tuple[Tuple[Optional[str], float]]]]`): Attribute holding _cache data.
  - `_pending_queries` (`Dict[Tuple[Tuple[Tuple[str, str]], asyncio.Event]]`): Attribute holding _pending_queries data.

- **Methods**:
  - `__init__(bot: Any, top_k: int, max_chars: int, max_cache_size: int, cache_ttl: float) -> None`: Executes __init__ logic.
  - `invalidate(channel_id: str) -> None`: Invalidate all cached episodic queries for a specific channel.
  - `get(message: discord.Message) -> Optional[str]`: Return formatted episodic context string, or None if nothing relevant.

## Functions

No top-level functions defined.
