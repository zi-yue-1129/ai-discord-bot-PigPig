# File: `cogs/memory/db/episodic_storage.py`

## Overview
EpisodicStorage: handles message-related tables (messages, pending_messages, messages_archive).

Extracted from the previous sqlite_storage implementation to separate concerns.
All error reporting uses func.report_error per project rules.

## Classes

### `EpisodicStorage`
Handles channel memory state management.

- **Attributes**:
  - `db` (`Any`): Instance attribute managing db.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `initialize_channel_memory_state() -> None`: Initialize the channel_memory_state table in the database.
  - `get_channel_memory_state(channel_id) -> Optional[Dict[Tuple[str, int]]]`: Get the memory state for a specific channel.  Args:     channel_id (int): The channel ID to get state for.      Returns:     Optional[Dict[str, int]]: Dictionary with 'message_count' and 'start_message_id', or None if not found.
  - `update_channel_memory_state(channel_id, message_count, start_message_id, last_summary_timestamp, last_summary_text) -> None`: Update the memory state for a specific channel.  Args:     channel_id (int): The channel ID to update state for.     message_count (int): The new message count.     start_message_id (int): The start message ID.     last_summary_timestamp (Optional[float]): Timestamp of last summary. If None, keeps existing value.     last_summary_text (Optional[str]): Text of last summary. If None, keeps existing value.
  - `get_total_count() -> int`: Return total number of channel memory states stored.
