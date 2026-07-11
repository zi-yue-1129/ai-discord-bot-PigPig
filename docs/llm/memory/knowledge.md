# File: `llm/memory/knowledge.py`

## Overview
The `KnowledgeMemoryProvider` handles "Shared Knowledge" at the server (Guild) or Channel level. This is used for storing community-specific information such as:
- **Server Rules**: Custom instructions for the bot within a specific guild.
- **Inside Jokes/Memes**: Information that applies to everyone in a channel.
- **Local Facts**: Information about a specific community or project.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `knowledge.py`, providing vital integrations within the PigPig bot ecosystem.
KnowledgeMemoryProvider: provides guild and channel level knowledge with caching.

This provider handles retrieval of shared interaction knowledge (memes, facts, etc.)
and implements a TTL cache to optimize performance during message orchestration.

## Classes

### `KnowledgeMemory`
Represents the fetched knowledge for a specific context.

- **Attributes**:
  - `guild_knowledge` (`Any`): Internal instance state.
  - `channel_knowledge` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(guild_knowledge: Optional[str], channel_knowledge: Optional[str]) -> Any`: Performs internal processing logic.

### `KnowledgeMemoryProvider`
Provides guild/channel knowledge with caching.

- **Attributes**:
  - `storage` (`Any`): Internal instance state.
  - `max_cache_size` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(storage: KnowledgeStorage, max_cache_size: int) -> None`: Initialize with storage and cache limit.
  - `get(guild_id: Optional[str], channel_id: str) -> KnowledgeMemory`: Fetch knowledge for the current guild and channel.
  - `_get_single(target_type: str, target_id: str) -> Optional[str]`: Internal helper with TTL cache and thundering herd protection.
  - `invalidate(target_type: str, target_id: str) -> None`: Invalidate cache for a specific target.
