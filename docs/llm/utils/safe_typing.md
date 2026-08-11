# File: `llm/utils/safe_typing.py`

## Overview
Core responsibilities and logic for `llm/utils/safe_typing.py`. This module is part of the llm subsystem and handles the associated business logic, state management, and integrations.

## Classes

### `SafeTyping`
Typing indicator that handles per-channel deduplication and rate-limiting.

This class ensures that only one typing heart-beat loop is running per channel,
even if multiple tasks are processing messages for the same channel.
It also enforces a minimum interval between trigger_typing() calls and
handles 429 rate limits gracefully.

- **Attributes**:
  - `_sessions` (`Dict[Tuple[int, int]]`): Stores data related to _sessions.
  - `_tasks` (`Dict[Tuple[int, asyncio.Task]]`): Stores data related to _tasks.
  - `_last_trigger` (`Dict[Tuple[int, float]]`): Stores data related to _last_trigger.
  - `_channel` (`Any`): Instance attribute managing _channel.
  - `_channel_id` (`Any`): Instance attribute managing _channel_id.
