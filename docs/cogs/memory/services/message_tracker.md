# File: `cogs/memory/services/message_tracker.py`

## Overview
Core file handling responsibilities within the `cogs/memory/services` subsystem.

## Classes

### `MessageTracker`
Tracks new messages in channels for the memory system.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: str, storage: str, settings: MemoryConfig) -> Any`: Initializes the MessageTracker.
  - `track_message(message: discord.Message) -> Any`: Tracks a message, adding it to the pending list if it's not from a bot
  - `_schedule_processing(channel: Union[Tuple[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread]]) -> Any`: Schedules channel memory processing with a debounce delay.
  - `interrupt_all() -> Any`: Interrupts all pending and active memory processing tasks.
  - `_process_channel_memory(channel: Union[Tuple[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread]]) -> Any`: Processes memory for a channel when threshold is reached.
  - `get_pending_count() -> int`: Gets the current count of pending messages.
  - `reset_pending_count() -> Any`: Resets the pending message count to zero.

## Functions

### `discord_id_to_unix_timestamp(message_id: int) -> float`
Convert Discord message ID to Unix timestamp in milliseconds.
