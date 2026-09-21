# File: `cogs/memory/interfaces/storage_interface.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `ProceduralStorageInterface`
Interface for procedural (user) storage operations.

- **Attributes**:
  - None specified.

- **Methods**:
  - `get_user_info(discord_id: str) -> Optional[UserInfo]`: Executes get_user_info logic.
  - `delete_user_data(discord_id: str) -> bool`: Executes delete_user_data logic.
  - `update_user_data(discord_id: str, discord_name: str, procedural_memory: Optional[str], user_background: Optional[str], display_names: Optional[List[str]], nickname: Optional[str]) -> bool`: Executes update_user_data logic.
  - `update_user_activity(discord_id: str, discord_name: str, nickname: Optional[str]) -> bool`: Executes update_user_activity logic.
  - `get_config(key: str) -> Optional[str]`: Executes get_config logic.
  - `set_config(key: str, value: str) -> None`: Executes set_config logic.
  - `get_all_users(limit: int, offset: int) -> List[UserInfo]`: Executes get_all_users logic.
  - `get_users_count() -> int`: Executes get_users_count logic.

### `EpisodicStorageInterface`
Interface for episodic (channel memory state) storage operations.

- **Attributes**:
  - None specified.

- **Methods**:
  - `initialize_channel_memory_state() -> None`: Initialize the channel_memory_state table in the database.
  - `get_channel_memory_state(channel_id: int) -> Optional[Dict[Tuple[str, int]]]`: Get the memory state for a specific channel.
  - `update_channel_memory_state(channel_id: int, message_count: int, start_message_id: int, last_summary_timestamp: Optional[float], last_summary_text: Optional[str]) -> None`: Update the memory state for a specific channel.

### `StorageInterface`
Combined interface kept for backward compatibility.

- **Attributes**:
  - None specified.

- **Methods**:
  - None specified.

## Functions

No top-level functions defined.
