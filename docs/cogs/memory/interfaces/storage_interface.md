# File: `cogs/memory/interfaces/storage_interface.py`

## Overview
Core file handling responsibilities within the `cogs/memory/interfaces` subsystem.

## Classes

### `ProceduralStorageInterface`
Interface for procedural (user) storage operations.

- **Attributes**:
  - None specified.

- **Methods**:
  - `get_user_info(discord_id: str) -> Optional[str]`: No description provided.
  - `delete_user_data(discord_id: str) -> bool`: No description provided.
  - `update_user_data(discord_id: str, discord_name: str, procedural_memory: Optional[str], user_background: Optional[str], display_names: Optional[List[str]], nickname: Optional[str]) -> bool`: No description provided.
  - `update_user_activity(discord_id: str, discord_name: str, nickname: Optional[str]) -> bool`: No description provided.
  - `get_config(key: str) -> Optional[str]`: No description provided.
  - `set_config(key: str, value: str) -> None`: No description provided.
  - `get_all_users(limit: int, offset: int) -> List[str]`: No description provided.
  - `get_users_count() -> int`: No description provided.

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

No module-level functions defined in this file.
