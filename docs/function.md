# File: `function.py`

## Overview
This file is part of the core application entry points and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `function.py`.

## Classes

### `ErrorDeduplicator`
Tracks recently reported errors to avoid sending duplicates to Discord.  Uses a hash of error type + message + details to identify unique errors. Errors within the cooldown period are suppressed.  Attributes:     _recent_errors: Dict mapping error keys to (timestamp, count).     _cooldown_seconds: Minimum seconds between reports of the same error.     _lock: Threading lock for thread-safe operations.

- **Attributes**:
  - `_recent_errors` (`Dict[str, tuple[float, int]]`): Instance attribute _recent_errors
  - `_cooldown_seconds` (`Any`): Instance attribute _cooldown_seconds
  - `_lock` (`Any`): Instance attribute _lock
  - `_cleanup_threshold` (`Any`): Instance attribute _cleanup_threshold

- **Methods**:
  - `_make_key(self, error, details) -> str`: Create a unique key for the error.  Args:     error: The exception object.     details: Additional context details.      Returns:     A hash string identifying this error type + message combination.
  - `should_report(self, error, details) -> bool`: Check if this error should be reported or suppressed as duplicate.  Args:     error: The exception to check.     details: Additional context for the error.      Returns:     True if the error should be reported, False if it's a duplicate.
  - `get_suppressed_count(self, error, details) -> int`: Get the number of times this error was suppressed since last report.  Args:     error: The exception to check.     details: Additional context for the error.      Returns:     Number of suppressed duplicates (0 if first occurrence).
  - `_cleanup(self, current_time) -> None`: Remove expired entries from the cache.  Args:     current_time: Current monotonic time for expiry comparison.

### `Function`
Class representing Function.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot

- **Methods**:
  - `set_bot(self, bot) -> Any`: Method set_bot.
  - `report_error(self, error, details) -> Any`: Report an error to Discord with deduplication.  Prevents the same error from being sent multiple times within a cooldown period. If an error is suppressed, it will be logged locally but not sent to Discord.  Quota/rate limit errors are logged as WARNING instead of ERROR.  Args:     error: The exception to report.     details: Additional context about where the error occurred.
  - `open_json(self, path) -> dict`: Method open_json.
  - `update_json(self, path, new_data) -> None`: Method update_json.

## Functions

### `get_error_deduplicator() -> ErrorDeduplicator`
Get the global ErrorDeduplicator singleton.

