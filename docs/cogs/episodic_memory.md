# File: `cogs/episodic_memory.py`

## Overview
The EpisodicMemory cog provides advanced memory management and context retention capabilities for Discord users. It enables users to store, retrieve, and manage personal memories, conversation history, and contextual information across sessions with intelligent search, organization, and recall features.

## Classes

### `EpisodicMemoryService`
A background service responsible for the first stage of the ETL process
for episodic memory. It fetches full message objects from Discord's API
based on pending messages tracked by the MessageTracker.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `is_processing` (`Any`): Instance attribute managing is_processing.

- **Methods**:
  - `cog_load() -> None`: Load the episodic memory service.
  - `cog_unload() -> None`: Unload the episodic memory service.
  - `force_update_memory(interaction) -> Any`: Force update the memory for the current channel. Owner only.
  - `search_episodic_memory(interaction, vector_query, keyword_query, user_id, channel_id) -> Any`: Search episodic memory with multiple query parameters. Owner only.

## Functions

### `setup(bot) -> Any`
The setup function for the cog.

