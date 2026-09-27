# File: `cogs/memory/services/message_tracker.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `message_tracker` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `MessageTracker`
Tracks new messages in channels for the memory system.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `storage` (`Any`): Instance attribute for storage.
  - `settings` (`Any`): Instance attribute for settings.
  - `_pending_message_count` (`Any`): Instance attribute for _pending_message_count.
  - `_processing_tasks` (`Any`): Instance attribute for _processing_tasks.
  - `_processing_semaphore` (`Any`): Instance attribute for _processing_semaphore.
  - `_active_summarization_task` (`Any`): Instance attribute for _active_summarization_task.

- **Methods**:
  - `__init__(bot, storage, settings) -> Any`: Initializes the MessageTracker.
  - `track_message(message) -> Any`: Tracks a message, adding it to the pending list if it's not from a bot
  - `_schedule_processing(channel) -> Any`: Schedules channel memory processing with a debounce delay.
  - `interrupt_all() -> Any`: Interrupts all pending and active memory processing tasks.
  - `_process_channel_memory(channel) -> Any`: Processes memory for a channel when threshold is reached.
  - `get_pending_count() -> int`: Gets the current count of pending messages.
  - `reset_pending_count() -> Any`: Resets the pending message count to zero.

## Functions

### `discord_id_to_unix_timestamp(message_id) -> float`
Convert Discord message ID to Unix timestamp in milliseconds.
