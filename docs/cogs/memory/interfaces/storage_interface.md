# File: `cogs/memory/interfaces/storage_interface.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `storage_interface` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `ProceduralStorageInterface`
Interface for procedural (user) storage operations.

- **Methods**:
  - `get_user_info(discord_id) -> Optional[...]`: Handles the `get_user_info` functionality. Executes the underlying business logic for this operation.
  - `delete_user_data(discord_id) -> bool`: Handles the `delete_user_data` functionality. Executes the underlying business logic for this operation.
  - `update_user_data(discord_id, discord_name, procedural_memory, user_background, display_names, nickname) -> bool`: Handles the `update_user_data` functionality. Executes the underlying business logic for this operation.
  - `update_user_activity(discord_id, discord_name, nickname) -> bool`: Handles the `update_user_activity` functionality. Executes the underlying business logic for this operation.
  - `get_config(key) -> Optional[...]`: Handles the `get_config` functionality. Executes the underlying business logic for this operation.
  - `set_config(key, value) -> None`: Handles the `set_config` functionality. Executes the underlying business logic for this operation.
  - `get_all_users(limit, offset) -> List[...]`: Handles the `get_all_users` functionality. Executes the underlying business logic for this operation.
  - `get_users_count() -> int`: Handles the `get_users_count` functionality. Executes the underlying business logic for this operation.

### `EpisodicStorageInterface`
Interface for episodic (channel memory state) storage operations.

- **Methods**:
  - `initialize_channel_memory_state() -> None`: Initialize the channel_memory_state table in the database.
  - `get_channel_memory_state(channel_id) -> Optional[...]`: Get the memory state for a specific channel.
  - `update_channel_memory_state(channel_id, message_count, start_message_id, last_summary_timestamp, last_summary_text) -> None`: Update the memory state for a specific channel.

### `StorageInterface`
Combined interface kept for backward compatibility.
