# File: `cogs/memory/db/episodic_storage.py`

## Overview
EpisodicStorage: handles message-related tables (messages, pending_messages, messages_archive).

Extracted from the previous sqlite_storage implementation to separate concerns.
All error reporting uses func.report_error per project rules.

## Classes

### `EpisodicStorage`
Handles channel memory state management.

- **Attributes**:
  - `db` (`Any`): Attribute holding db data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(db: DatabaseConnection) -> None`: Executes __init__ logic.
  - `initialize_channel_memory_state() -> None`: Initialize the channel_memory_state table in the database.
  - `_initialize_channel_memory_state_sync() -> None`: Executes _initialize_channel_memory_state_sync logic.
  - `get_channel_memory_state(channel_id: int) -> Optional[Dict[Tuple[str, int]]]`: Get the memory state for a specific channel.
  - `_get_channel_memory_state_sync(channel_id: int) -> Optional[Dict[Tuple[str, Any]]]`: Executes _get_channel_memory_state_sync logic.
  - `update_channel_memory_state(channel_id: int, message_count: int, start_message_id: int, last_summary_timestamp: Optional[float], last_summary_text: Optional[str]) -> None`: Update the memory state for a specific channel.
  - `_update_channel_memory_state_sync(channel_id: int, message_count: int, start_message_id: int, last_summary_timestamp: Optional[float], last_summary_text: Optional[str]) -> None`: Executes _update_channel_memory_state_sync logic.
  - `get_total_count() -> int`: Return total number of channel memory states stored.
  - `_get_total_count_sync() -> int`: Executes _get_total_count_sync logic.

## Functions

No top-level functions defined.
