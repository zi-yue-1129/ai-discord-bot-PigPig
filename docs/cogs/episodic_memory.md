# File: `cogs/episodic_memory.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `episodic_memory` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `EpisodicMemoryService`
A background service responsible for the first stage of the ETL process
for episodic memory. It fetches full message objects from Discord's API
based on pending messages tracked by the MessageTracker.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `storage` (`StorageInterface`): Instance attribute for storage.
  - `settings` (`MemoryConfig`): Instance attribute for settings.
  - `message_tracker` (`MessageTracker`): Instance attribute for message_tracker.
  - `is_processing` (`Any`): Instance attribute for is_processing.

- **Methods**:
  - `__init__(bot, storage) -> Any`: Args:
  - `cog_load() -> None`: Load the episodic memory service.
  - `cog_unload() -> None`: Unload the episodic memory service.
  - `_translate_text(lang_manager, guild_id, *args, **kwargs) -> str`: Helper method to safely translate text with fallback.
  - `force_update_memory(interaction) -> Any`: Force update the memory for the current channel. Owner only.
  - `search_episodic_memory(interaction, vector_query, keyword_query, user_id, channel_id) -> Any`: Search episodic memory with multiple query parameters. Owner only.

## Functions

### `setup(bot) -> Any`
The setup function for the cog.
