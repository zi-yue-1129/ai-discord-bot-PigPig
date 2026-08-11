# File: `function.py`

## Overview
The `function.py` module provides a global utility singleton (`func`) and error management tools used throughout the entire bot ecosystem.

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
  - `_cooldown_seconds` (`Any`): Instance attribute managing _cooldown_seconds.
  - `_lock` (`Any`): Instance attribute managing _lock.
  - `_cleanup_threshold` (`Any`): Instance attribute managing _cleanup_threshold.

- **Methods**:
  - `should_report(error, details) -> bool`: Check if this error should be reported or suppressed as duplicate.  Args:     error: The exception to check.     details: Additional context for the error.      Returns:     True if the error should be reported, False if it's a duplicate.
  - `get_suppressed_count(error, details) -> int`: Get the number of times this error was suppressed since last report.  Args:     error: The exception to check.     details: Additional context for the error.      Returns:     Number of suppressed duplicates (0 if first occurrence).

### `Function`
Manages the state and core operations for Function.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.

- **Methods**:
  - `report_error(error, details) -> Any`: Report an error to Discord with deduplication.  Prevents the same error from being sent multiple times within a cooldown period. If an error is suppressed, it will be logged locally but not sent to Discord.  Quota/rate limit errors are logged as WARNING instead of ERROR.  Args:     error: The exception to report.     details: Additional context about where the error occurred.
  - `open_json(path) -> dict`: Executes logic for open_json.
  - `update_json(path, new_data) -> None`: Executes logic for update_json.

## Functions

### `get_error_deduplicator() -> ErrorDeduplicator`
Get the global ErrorDeduplicator singleton.

