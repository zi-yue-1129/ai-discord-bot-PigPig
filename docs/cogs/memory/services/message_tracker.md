# File: `cogs/memory/services/message_tracker.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/memory/services/message_tracker.py`.

## Classes

### `MessageTracker`
Tracks new messages in channels for the memory system.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `storage` (`Any`): Instance attribute storage
  - `settings` (`Any`): Instance attribute settings
  - `_pending_message_count` (`Any`): Instance attribute _pending_message_count
  - `_processing_tasks` (`Any`): Instance attribute _processing_tasks
  - `_processing_semaphore` (`Any`): Instance attribute _processing_semaphore
  - `_active_summarization_task` (`Any`): Instance attribute _active_summarization_task

- **Methods**:
  - `track_message(self, message) -> Any`: Tracks a message, adding it to the pending list if it's not from a bot and not in an excluded channel. Also updates channel memory state.  Args:     message (discord.Message): The message to track.
  - `_schedule_processing(self, channel) -> Any`: Schedules channel memory processing with a debounce delay. This prevents the background LLM task from competing with  the immediate reply generation triggered just after this.
  - `interrupt_all(self) -> Any`: Interrupts all pending and active memory processing tasks. This is called when a high-priority conversation task (handle_message) starts.
  - `_process_channel_memory(self, channel) -> Any`: Processes memory for a channel when threshold is reached.  Args:     channel (discord.TextChannel): The channel to process memory for.
  - `get_pending_count(self) -> int`: Gets the current count of pending messages.  Returns:     int: The number of pending messages.
  - `reset_pending_count(self) -> Any`: Resets the pending message count to zero.

## Functions

### `discord_id_to_unix_timestamp(message_id) -> float`
Convert Discord message ID to Unix timestamp in milliseconds.  Args:     message_id (int): The Discord message ID      Returns:     float: The Unix timestamp in milliseconds when the message was created
