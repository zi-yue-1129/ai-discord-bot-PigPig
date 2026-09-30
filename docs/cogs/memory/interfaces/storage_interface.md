# File: `cogs/memory/interfaces/storage_interface.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/memory/interfaces/storage_interface.py`.

## Classes

### `ProceduralStorageInterface`
Interface for procedural (user) storage operations.

- **Attributes**:
  - None

- **Methods**:
  - `get_user_info(self, discord_id) -> Optional['UserInfo']`: Method get_user_info.
  - `delete_user_data(self, discord_id) -> bool`: Method delete_user_data.
  - `update_user_data(self, discord_id, discord_name, procedural_memory, user_background, display_names, nickname) -> bool`: Method update_user_data.
  - `update_user_activity(self, discord_id, discord_name, nickname) -> bool`: Method update_user_activity.
  - `get_config(self, key) -> Optional[str]`: Method get_config.
  - `set_config(self, key, value) -> None`: Method set_config.
  - `get_all_users(self, limit, offset) -> List['UserInfo']`: Method get_all_users.
  - `get_users_count(self) -> int`: Method get_users_count.

### `EpisodicStorageInterface`
Interface for episodic (channel memory state) storage operations.

- **Attributes**:
  - None

- **Methods**:
  - `initialize_channel_memory_state(self) -> None`: Initialize the channel_memory_state table in the database.
  - `get_channel_memory_state(self, channel_id) -> Optional[Dict[str, int]]`: Get the memory state for a specific channel.  Args:     channel_id (int): The channel ID to get state for.      Returns:     Optional[Dict[str, int]]: Dictionary with 'message_count' and 'start_message_id', or None if not found.
  - `update_channel_memory_state(self, channel_id, message_count, start_message_id, last_summary_timestamp, last_summary_text) -> None`: Update the memory state for a specific channel.  Args:     channel_id (int): The channel ID to update state for.     message_count (int): The new message count.     start_message_id (int): The start message ID.     last_summary_timestamp (Optional[float]): Timestamp of last summary.     last_summary_text (Optional[str]): Text of last summary.

### `StorageInterface`
Combined interface kept for backward compatibility.

- **Attributes**:
  - None

- **Methods**:
  - None

## Functions

None
