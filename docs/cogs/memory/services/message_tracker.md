# File: `cogs/memory/services/message_tracker.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `MessageTracker`
Tracks new messages in channels for the memory system.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `storage` (`Any`): Attribute holding storage data.
  - `settings` (`Any`): Attribute holding settings data.
  - `_pending_message_count` (`Any`): Attribute holding _pending_message_count data.
  - `_processing_tasks` (`Any`): Attribute holding _processing_tasks data.
  - `_processing_semaphore` (`Any`): Attribute holding _processing_semaphore data.
  - `_active_summarization_task` (`Any`): Attribute holding _active_summarization_task data.

- **Methods**:
  - `__init__(bot: Bot, storage: StorageInterface, settings: MemoryConfig) -> Any`: Initializes the MessageTracker.
  - `track_message(message: discord.Message) -> Any`: Tracks a message, adding it to the pending list if it's not from a bot
  - `_schedule_processing(channel: Union[Tuple[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread]]) -> Any`: Schedules channel memory processing with a debounce delay.
  - `interrupt_all() -> Any`: Interrupts all pending and active memory processing tasks.
  - `_process_channel_memory(channel: Union[Tuple[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread]]) -> Any`: Processes memory for a channel when threshold is reached.
  - `get_pending_count() -> int`: Gets the current count of pending messages.
  - `reset_pending_count() -> Any`: Resets the pending message count to zero.

## Functions

### `discord_id_to_unix_timestamp(message_id: int) -> float`
Convert Discord message ID to Unix timestamp in milliseconds.

Args:
    message_id (int): The Discord message ID

Returns:
    float: The Unix timestamp in milliseconds when the message was created
