# File: `llm/utils/safe_typing.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `safe_typing` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `SafeTyping`
Typing indicator that handles per-channel deduplication and rate-limiting.

This class ensures that only one typing heart-beat loop is running per channel,
even if multiple tasks are processing messages for the same channel.
It also enforces a minimum interval between trigger_typing() calls and
handles 429 rate limits gracefully.

- **Attributes**:
  - `_sessions` (`Dict[...]`): Class attribute representing _sessions.
  - `_tasks` (`Dict[...]`): Class attribute representing _tasks.
  - `_last_trigger` (`Dict[...]`): Class attribute representing _last_trigger.
  - `_lock` (`Any`): Class attribute representing _lock.
  - `_INTERVAL` (`Any`): Class attribute representing _INTERVAL.
  - `_BACKOFF` (`Any`): Class attribute representing _BACKOFF.
  - `_MIN_CALL_DELAY` (`Any`): Class attribute representing _MIN_CALL_DELAY.
  - `_channel` (`Any`): Instance attribute for _channel.
  - `_channel_id` (`Any`): Instance attribute for _channel_id.

- **Methods**:
  - `__init__(channel) -> None`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `_loop(channel_id) -> None`: Background loop to keep the typing indicator alive.
