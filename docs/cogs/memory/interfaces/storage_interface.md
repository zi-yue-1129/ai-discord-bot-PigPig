# File: `cogs/memory/interfaces/storage_interface.py`

## Overview
Core logic and functionalities for storage_interface.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Classes

### `ProceduralStorageInterface`
Interface for procedural (user) storage operations.

- **Methods**:
  - `get_user_info(discord_id) -> Optional[UserInfo]`: Executes get_user_info operation.
  - `delete_user_data(discord_id) -> bool`: Executes delete_user_data operation.
  - `update_user_data(discord_id, discord_name, procedural_memory, user_background, display_names, nickname) -> bool`: Executes update_user_data operation.
  - `update_user_activity(discord_id, discord_name, nickname) -> bool`: Executes update_user_activity operation.
  - `get_config(key) -> Optional[str]`: Executes get_config operation.
  - `set_config(key, value) -> None`: Executes set_config operation.
  - `get_all_users(limit, offset) -> List[UserInfo]`: Executes logic for get_all_users.
  - `get_users_count() -> int`: Executes logic for get_users_count.

### `EpisodicStorageInterface`
Interface for episodic (channel memory state) storage operations.

- **Methods**:
  - `initialize_channel_memory_state() -> None`: Initialize the channel_memory_state table in the database.
  - `get_channel_memory_state(channel_id) -> Optional[Dict[Tuple[str, int]]]`: Get the memory state for a specific channel.  Args:     channel_id (int): The channel ID to get state for.      Returns:     Optional[Dict[str, int]]: Dictionary with 'message_count' and 'start_message_id', or None if not found.
  - `update_channel_memory_state(channel_id, message_count, start_message_id, last_summary_timestamp, last_summary_text) -> None`: Update the memory state for a specific channel.  Args:     channel_id (int): The channel ID to update state for.     message_count (int): The new message count.     start_message_id (int): The start message ID.     last_summary_timestamp (Optional[float]): Timestamp of last summary.     last_summary_text (Optional[str]): Text of last summary.

### `StorageInterface`
Combined interface kept for backward compatibility.
