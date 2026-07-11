# File: `function.py`

## Overview
The `function.py` module provides a global utility singleton (`func`) and error management tools used throughout the entire bot ecosystem.

This file belongs to the Core System. Its core responsibility is to handle logic related to `function.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `ErrorDeduplicator`
Tracks recently reported errors to avoid sending duplicates to Discord.

Uses a hash of error type + message + details to identify unique errors.
Errors within the cooldown period are suppressed.

Attributes:
    _recent_errors: Dict mapping error keys to (timestamp, count).
    _cooldown_seconds: Minimum seconds between reports of the same error.
    _lock: Threading lock for thread-safe operations.

- **Attributes**:
  - `_cooldown_seconds` (`Any`): Internal instance state.
  - `_lock` (`Any`): Internal instance state.
  - `_cleanup_threshold` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(cooldown_seconds: float) -> None`: Initialize the error deduplicator.
  - `_make_key(error: Exception, details: Optional[str]) -> str`: Create a unique key for the error.
  - `should_report(error: Exception, details: Optional[str]) -> bool`: Check if this error should be reported or suppressed as duplicate.
  - `get_suppressed_count(error: Exception, details: Optional[str]) -> int`: Get the number of times this error was suppressed since last report.
  - `_cleanup(current_time: float) -> None`: Remove expired entries from the cache.

### `Function`
Class managing Function state and behavior.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.

- **Methods**:
  - `__init__() -> Any`: Performs internal processing logic.
  - `set_bot(bot: Any) -> Any`: Performs internal processing logic.
  - `report_error(error: Exception, details: str) -> Any`: Report an error to Discord with deduplication.
  - `open_json(path: str) -> dict`: Performs internal processing logic.
  - `update_json(path: str, new_data: dict) -> None`: Performs internal processing logic.

## Functions

### `get_error_deduplicator() -> ErrorDeduplicator`
Get the global ErrorDeduplicator singleton.
