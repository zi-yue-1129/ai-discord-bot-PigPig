# File: `cogs/memory/services/message_tracker.py`

## Overview
Core logic and functionalities for message_tracker.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Classes

### `MessageTracker`
Tracks new messages in channels for the memory system.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `storage` (`Any`): Instance attribute managing storage.
  - `settings` (`Any`): Instance attribute managing settings.
  - `_pending_message_count` (`Any`): Instance attribute managing _pending_message_count.
  - `_processing_tasks` (`Any`): Instance attribute managing _processing_tasks.
  - `_processing_semaphore` (`Any`): Instance attribute managing _processing_semaphore.
  - `_active_summarization_task` (`Any`): Instance attribute managing _active_summarization_task.

- **Methods**:
  - `track_message(message) -> Any`: Tracks a message, adding it to the pending list if it's not from a bot and not in an excluded channel. Also updates channel memory state.  Args:     message (discord.Message): The message to track.
  - `interrupt_all() -> Any`: Interrupts all pending and active memory processing tasks. This is called when a high-priority conversation task (handle_message) starts.
  - `get_pending_count() -> int`: Gets the current count of pending messages.  Returns:     int: The number of pending messages.
  - `reset_pending_count() -> Any`: Resets the pending message count to zero.

## Functions

### `discord_id_to_unix_timestamp(message_id) -> float`
Convert Discord message ID to Unix timestamp in milliseconds.

Args:
    message_id (int): The Discord message ID

Returns:
    float: The Unix timestamp in milliseconds when the message was created
