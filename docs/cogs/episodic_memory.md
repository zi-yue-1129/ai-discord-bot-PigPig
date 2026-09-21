# File: `cogs/episodic_memory.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `EpisodicMemoryService`
A background service responsible for the first stage of the ETL process
for episodic memory. It fetches full message objects from Discord's API
based on pending messages tracked by the MessageTracker.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `storage` (`StorageInterface`): Attribute holding storage data.
  - `settings` (`MemoryConfig`): Attribute holding settings data.
  - `message_tracker` (`MessageTracker`): Attribute holding message_tracker data.
  - `is_processing` (`Any`): Attribute holding is_processing data.

- **Methods**:
  - `__init__(bot: PigPig | commands.Bot, storage: StorageInterface) -> Any`: Args:
  - `cog_load() -> None`: Load the episodic memory service.
  - `cog_unload() -> None`: Unload the episodic memory service.
  - `_translate_text(lang_manager: Any, guild_id: str, *args, **kwargs) -> str`: Helper method to safely translate text with fallback.
  - `force_update_memory(interaction: discord.Interaction) -> Any`: Force update the memory for the current channel. Owner only.
  - `search_episodic_memory(interaction: discord.Interaction, vector_query: Optional[str], keyword_query: Optional[str], user_id: Optional[str], channel_id: Optional[str]) -> Any`: Search episodic memory with multiple query parameters. Owner only.

## Functions

### `setup(bot: commands.Bot) -> Any`
The setup function for the cog.
