# File: `llm/utils/safe_typing.py`

## Overview
This file is part of the LLM integration and orchestration pipeline and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `llm/utils/safe_typing.py`.

## Classes

### `SafeTyping`
Typing indicator that handles per-channel deduplication and rate-limiting.  This class ensures that only one typing heart-beat loop is running per channel, even if multiple tasks are processing messages for the same channel. It also enforces a minimum interval between trigger_typing() calls and handles 429 rate limits gracefully.

- **Attributes**:
  - `_sessions` (`Dict[int, int]`): Attribute _sessions
  - `_tasks` (`Dict[int, asyncio.Task]`): Attribute _tasks
  - `_last_trigger` (`Dict[int, float]`): Attribute _last_trigger
  - `_lock` (`Any`): Attribute _lock
  - `_INTERVAL` (`Any`): Attribute _INTERVAL
  - `_BACKOFF` (`Any`): Attribute _BACKOFF
  - `_MIN_CALL_DELAY` (`Any`): Attribute _MIN_CALL_DELAY
  - `_channel` (`Any`): Instance attribute _channel
  - `_channel_id` (`Any`): Instance attribute _channel_id

- **Methods**:
  - `_loop(self, channel_id) -> None`: Background loop to keep the typing indicator alive.

## Functions

None
