# File: `cogs/memory/db/episodic_storage.py`

## Overview
EpisodicStorage: handles message-related tables (messages, pending_messages, messages_archive).

Extracted from the previous sqlite_storage implementation to separate concerns.
All error reporting uses func.report_error per project rules.

## Classes

### `EpisodicStorage`
Handles channel memory state management.

- **Attributes**:
  - `db` (`Any`): Instance attribute for db.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(db) -> None`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `initialize_channel_memory_state() -> None`: Initialize the channel_memory_state table in the database.
  - `_initialize_channel_memory_state_sync() -> None`: Handles the `_initialize_channel_memory_state_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
  - `get_channel_memory_state(channel_id) -> Optional[...]`: Get the memory state for a specific channel.
  - `_get_channel_memory_state_sync(channel_id) -> Optional[...]`: Handles the `_get_channel_memory_state_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
  - `update_channel_memory_state(channel_id, message_count, start_message_id, last_summary_timestamp, last_summary_text) -> None`: Update the memory state for a specific channel.
  - `_update_channel_memory_state_sync(channel_id, message_count, start_message_id, last_summary_timestamp, last_summary_text) -> None`: Handles the `_update_channel_memory_state_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
  - `get_total_count() -> int`: Return total number of channel memory states stored.
  - `_get_total_count_sync() -> int`: Handles the `_get_total_count_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
