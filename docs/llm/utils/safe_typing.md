# File: `llm/utils/safe_typing.py`

## Overview
Core file handling responsibilities within the `llm/utils` subsystem.

## Classes

### `SafeTyping`
Typing indicator that handles per-channel deduplication and rate-limiting.

- **Attributes**:
  - `_sessions` (`Dict[Tuple[int, int]]`): Class attribute
  - `_tasks` (`Dict[Tuple[int, asyncio.Task]]`): Class attribute
  - `_last_trigger` (`Dict[Tuple[int, float]]`): Class attribute

- **Methods**:
  - `__init__(channel: Any) -> None`: No description provided.
  - `_loop(channel_id: int) -> None`: Background loop to keep the typing indicator alive.

## Functions

No module-level functions defined in this file.
