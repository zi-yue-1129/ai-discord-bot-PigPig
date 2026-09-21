# File: `llm/utils/safe_typing.py`

## Overview
This file is part of the llm subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `SafeTyping`
Typing indicator that handles per-channel deduplication and rate-limiting.

This class ensures that only one typing heart-beat loop is running per channel,
even if multiple tasks are processing messages for the same channel.
It also enforces a minimum interval between trigger_typing() calls and
handles 429 rate limits gracefully.

- **Attributes**:
  - `_sessions` (`Dict[Tuple[int, int]]`): Attribute holding _sessions data.
  - `_tasks` (`Dict[Tuple[int, asyncio.Task]]`): Attribute holding _tasks data.
  - `_last_trigger` (`Dict[Tuple[int, float]]`): Attribute holding _last_trigger data.
  - `_channel` (`Any`): Attribute holding _channel data.
  - `_channel_id` (`Any`): Attribute holding _channel_id data.

- **Methods**:
  - `__init__(channel: Any) -> None`: Executes __init__ logic.
  - `_loop(channel_id: int) -> None`: Background loop to keep the typing indicator alive.

## Functions

No top-level functions defined.
