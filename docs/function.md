# File: `function.py`

## Overview
This file is part of the Core subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

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
  - `_recent_errors` (`Dict[Tuple[str, tuple[Tuple[float, int]]]]`): Attribute holding _recent_errors data.
  - `_cooldown_seconds` (`Any`): Attribute holding _cooldown_seconds data.
  - `_lock` (`Any`): Attribute holding _lock data.
  - `_cleanup_threshold` (`Any`): Attribute holding _cleanup_threshold data.

- **Methods**:
  - `__init__(cooldown_seconds: float) -> None`: Initialize the error deduplicator.
  - `_make_key(error: Exception, details: Optional[str]) -> str`: Create a unique key for the error.
  - `should_report(error: Exception, details: Optional[str]) -> bool`: Check if this error should be reported or suppressed as duplicate.
  - `get_suppressed_count(error: Exception, details: Optional[str]) -> int`: Get the number of times this error was suppressed since last report.
  - `_cleanup(current_time: float) -> None`: Remove expired entries from the cache.

### `Function`
Core class implementation.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.

- **Methods**:
  - `__init__() -> Any`: Executes __init__ logic.
  - `set_bot(bot) -> Any`: Executes set_bot logic.
  - `report_error(error: Exception, details: str) -> Any`: Report an error to Discord with deduplication.
  - `open_json(path: str) -> dict`: Executes open_json logic.
  - `update_json(path: str, new_data: dict) -> None`: Executes update_json logic.

## Functions

### `get_error_deduplicator() -> ErrorDeduplicator`
Get the global ErrorDeduplicator singleton.
