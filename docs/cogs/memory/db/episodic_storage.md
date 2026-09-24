# File: `cogs/memory/db/episodic_storage.py`

## Overview
EpisodicStorage: handles message-related tables (messages, pending_messages, messages_archive).

## Classes

### `EpisodicStorage`
Handles channel memory state management.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(db: DatabaseConnection) -> None`: No description provided.
  - `initialize_channel_memory_state() -> None`: Initialize the channel_memory_state table in the database.
  - `_initialize_channel_memory_state_sync() -> None`: No description provided.
  - `get_channel_memory_state(channel_id: int) -> Optional[Dict[Tuple[str, int]]]`: Get the memory state for a specific channel.
  - `_get_channel_memory_state_sync(channel_id: int) -> Optional[Dict[Tuple[str, Any]]]`: No description provided.
  - `update_channel_memory_state(channel_id: int, message_count: int, start_message_id: int, last_summary_timestamp: Optional[float], last_summary_text: Optional[str]) -> None`: Update the memory state for a specific channel.
  - `_update_channel_memory_state_sync(channel_id: int, message_count: int, start_message_id: int, last_summary_timestamp: Optional[float], last_summary_text: Optional[str]) -> None`: No description provided.
  - `get_total_count() -> int`: Return total number of channel memory states stored.
  - `_get_total_count_sync() -> int`: No description provided.

## Functions

No module-level functions defined in this file.
