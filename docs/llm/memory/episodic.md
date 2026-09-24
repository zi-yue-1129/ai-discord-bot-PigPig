# File: `llm/memory/episodic.py`

## Overview
Automatic Episodic Memory Provider for context injection.

## Classes

### `EpisodicMemoryProvider`
Retrieve semantically relevant past memory fragments for context injection.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: Any, top_k: int, max_chars: int, max_cache_size: int, cache_ttl: float) -> None`: No description provided.
  - `invalidate(channel_id: str) -> None`: Invalidate all cached episodic queries for a specific channel.
  - `get(message: discord.Message) -> Optional[str]`: Return formatted episodic context string, or None if nothing relevant.

## Functions

No module-level functions defined in this file.

