# File: `cogs/memory/db/episodic_storage.py`

## Overview
EpisodicStorage: handles message-related tables (messages, pending_messages, messages_archive).

Extracted from the previous sqlite_storage implementation to separate concerns.
All error reporting uses func.report_error per project rules.

## Classes

### `EpisodicStorage`
Handles channel memory state management.

- **Attributes**:
  - `db` (`Any`): Instance attribute db
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `initialize_channel_memory_state(self) -> None`: Initialize the channel_memory_state table in the database.
  - `_initialize_channel_memory_state_sync(self) -> None`: Method _initialize_channel_memory_state_sync.
  - `get_channel_memory_state(self, channel_id) -> Optional[Dict[str, int]]`: Get the memory state for a specific channel.  Args:     channel_id (int): The channel ID to get state for.      Returns:     Optional[Dict[str, int]]: Dictionary with 'message_count' and 'start_message_id', or None if not found.
  - `_get_channel_memory_state_sync(self, channel_id) -> Optional[Dict[str, Any]]`: Method _get_channel_memory_state_sync.
  - `update_channel_memory_state(self, channel_id, message_count, start_message_id, last_summary_timestamp, last_summary_text) -> None`: Update the memory state for a specific channel.  Args:     channel_id (int): The channel ID to update state for.     message_count (int): The new message count.     start_message_id (int): The start message ID.     last_summary_timestamp (Optional[float]): Timestamp of last summary. If None, keeps existing value.     last_summary_text (Optional[str]): Text of last summary. If None, keeps existing value.
  - `_update_channel_memory_state_sync(self, channel_id, message_count, start_message_id, last_summary_timestamp, last_summary_text) -> None`: Method _update_channel_memory_state_sync.
  - `get_total_count(self) -> int`: Return total number of channel memory states stored.
  - `_get_total_count_sync(self) -> int`: Method _get_total_count_sync.

## Functions

None
