# File: `cogs/episodic_memory.py`

## Overview
The EpisodicMemory cog provides advanced memory management and context retention capabilities for Discord users. It enables users to store, retrieve, and manage personal memories, conversation history, and contextual information across sessions with intelligent search, organization, and recall features.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `episodic_memory.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `EpisodicMemoryService`
A background service responsible for the first stage of the ETL process
for episodic memory. It fetches full message objects from Discord's API
based on pending messages tracked by the MessageTracker.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `is_processing` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: PigPig | commands.Bot, storage: StorageInterface) -> Any`: Args:
  - `cog_load() -> None`: Load the episodic memory service.
  - `cog_unload() -> None`: Unload the episodic memory service.
  - `_translate_text(lang_manager: Any, guild_id: str) -> str`: Helper method to safely translate text with fallback.
  - `force_update_memory(interaction: discord.Interaction) -> Any`: Force update the memory for the current channel. Owner only.
  - `search_episodic_memory(interaction: discord.Interaction, vector_query: Optional[str], keyword_query: Optional[str], user_id: Optional[str], channel_id: Optional[str]) -> Any`: Search episodic memory with multiple query parameters. Owner only.

## Functions

### `setup(bot: commands.Bot) -> Any`
The setup function for the cog.
