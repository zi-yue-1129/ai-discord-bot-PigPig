# File: `cogs/episodic_memory.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/episodic_memory.py`.

## Classes

### `EpisodicMemoryService`
A background service responsible for the first stage of the ETL process for episodic memory. It fetches full message objects from Discord's API based on pending messages tracked by the MessageTracker.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `storage` (`StorageInterface`): Instance attribute storage
  - `settings` (`MemoryConfig`): Instance attribute settings
  - `message_tracker` (`MessageTracker`): Instance attribute message_tracker
  - `is_processing` (`Any`): Instance attribute is_processing

- **Methods**:
  - `cog_load(self) -> None`: Load the episodic memory service.
  - `cog_unload(self) -> None`: Unload the episodic memory service.
  - `_translate_text(self, lang_manager, guild_id, *args, **kwargs) -> str`: Helper method to safely translate text with fallback.
  - `force_update_memory(self, interaction) -> Any`: Force update the memory for the current channel. Owner only.
  - `search_episodic_memory(self, interaction, vector_query, keyword_query, user_id, channel_id) -> Any`: Search episodic memory with multiple query parameters. Owner only.

## Functions

### `setup(bot) -> Any`
The setup function for the cog.

