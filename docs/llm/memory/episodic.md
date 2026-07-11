# File: `llm/memory/episodic.py`

## Overview
The `EpisodicMemoryProvider` implements a "long-term recall" mechanism. It uses semantic vector search to find past messages that are relevant to the user's current query, even if they occurred months ago.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `episodic.py`, providing vital integrations within the PigPig bot ecosystem.
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
  - `bot` (`Any`): Internal instance state.
  - `top_k` (`Any`): Internal instance state.
  - `max_chars` (`Any`): Internal instance state.
  - `max_cache_size` (`Any`): Internal instance state.
  - `cache_ttl` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any, top_k: int, max_chars: int, max_cache_size: int, cache_ttl: float) -> None`: Performs internal processing logic.
  - `invalidate(channel_id: str) -> None`: Invalidate all cached episodic queries for a specific channel.
  - `get(message: discord.Message) -> Optional[str]`: Return formatted episodic context string, or None if nothing relevant.
