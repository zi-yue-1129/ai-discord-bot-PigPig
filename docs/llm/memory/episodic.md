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
  - `bot` (`Any`): Instance attribute managing bot.
  - `top_k` (`Any`): Instance attribute managing top_k.
  - `max_chars` (`Any`): Instance attribute managing max_chars.
  - `max_cache_size` (`Any`): Instance attribute managing max_cache_size.
  - `cache_ttl` (`Any`): Instance attribute managing cache_ttl.

- **Methods**:
  - `invalidate(channel_id) -> None`: Invalidate all cached episodic queries for a specific channel.  Args:     channel_id: The Discord channel ID.
  - `get(message) -> Optional[str]`: Return formatted episodic context string, or None if nothing relevant.  Runs in parallel with ProceduralMemoryProvider via asyncio.gather in ContextManager, so it does not add serial latency to the pipeline.  Args:     message: Current Discord message (provides query text and channel scope).  Returns:     Formatted string with past memory fragments, or None.

