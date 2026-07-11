# File: `llm/utils/safe_typing.py`

## Overview
This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `safe_typing.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `SafeTyping`
Typing indicator that handles per-channel deduplication and rate-limiting.

This class ensures that only one typing heart-beat loop is running per channel,
even if multiple tasks are processing messages for the same channel.
It also enforces a minimum interval between trigger_typing() calls and
handles 429 rate limits gracefully.

- **Attributes**:
  - `_sessions` (`Dict[Tuple]`): Property holding the _sessions state.
  - `_tasks` (`Dict[Tuple]`): Property holding the _tasks state.
  - `_last_trigger` (`Dict[Tuple]`): Property holding the _last_trigger state.
  - `_channel` (`Any`): Internal instance state.
  - `_channel_id` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(channel: Any) -> None`: Performs core logic operations.
  - `_loop(channel_id: int) -> None`: Background loop to keep the typing indicator alive.
