# File: `addons/logging.py`

## Overview
This file is part of the `addons` subsystem. It is responsible for `logging` related functionality within the PigPig system, contributing to utility functions, configurations, and core extensions.

## Classes

### `LogRecord`
Structured log record following plan.md schema.

- **Attributes**:
  - `timestamp` (`str`): Class attribute representing timestamp.
  - `level` (`str`): Class attribute representing level.
  - `source` (`str`): Class attribute representing source.
  - `server_id` (`str`): Class attribute representing server_id.
  - `channel_or_file` (`str`): Class attribute representing channel_or_file.
  - `user_id` (`str`): Class attribute representing user_id.
  - `action` (`str`): Class attribute representing action.
  - `message` (`str`): Class attribute representing message.
  - `trace_id` (`Optional[...]`): Class attribute representing trace_id.
  - `extra` (`Dict[...]`): Class attribute representing extra.

- **Methods**:
  - `to_json_line() -> str`: Serialize record to a single NDJSON line.

### `BackgroundWriter`
Background single-thread writer that batches NDJSON records and writes per-level files.

- **Attributes**:
  - `_instance` (`Any`): Class attribute representing _instance.
  - `_instance_lock` (`Any`): Class attribute representing _instance_lock.
  - `batch_size` (`int`): Instance attribute for batch_size.
  - `flush_interval` (`float`): Instance attribute for flush_interval.
  - `queue_maxsize` (`int`): Instance attribute for queue_maxsize.
  - `_queue` (`Queue[Dict[str, Any]]`): Instance attribute for _queue.
  - `_thread` (`Any`): Instance attribute for _thread.
  - `_stop_event` (`Any`): Instance attribute for _stop_event.
  - `_metrics` (`Any`): Instance attribute for _metrics.

- **Methods**:
  - `__init__() -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `get` and `float`.
  - `get_instance(cls) -> BackgroundWriter`: Handles the `get_instance` functionality. Internally, it interacts with methods like `BackgroundWriter`.
  - `enqueue(server_id, level, json_line, timestamp_iso) -> None`: Attempt to enqueue a log event non-blocking. On full queue, drop and report.
  - `_report_error_async(exc, context) -> None`: Report errors through func.report_error if available, fallback to printing.
  - `stop(timeout) -> None`: Signal worker to stop and flush remaining items.
  - `_worker() -> None`: Worker loop: collect batches and perform grouped writes per server/date/level.

### `LoggerAdapter`
Logger-like object exposing bind(...) and level methods (info/warning/error/debug).

This provides a minimal structlog-like API for bindable context while delegating
actual output to BackgroundWriter and loguru console renderer.

- **Attributes**:
  - `_COLORS` (`Any`): Class attribute representing _COLORS.
  - `_LEVEL_EMOJI` (`Any`): Class attribute representing _LEVEL_EMOJI.
  - `DEBUG` (`Any`): Class attribute representing DEBUG.
  - `INFO` (`Any`): Class attribute representing INFO.
  - `WARNING` (`Any`): Class attribute representing WARNING.
  - `ERROR` (`Any`): Class attribute representing ERROR.
  - `CRITICAL` (`Any`): Class attribute representing CRITICAL.
  - `_LEVEL_NAME_TO_INT` (`Any`): Class attribute representing _LEVEL_NAME_TO_INT.
  - `server_id` (`Any`): Instance attribute for server_id.
  - `source` (`Any`): Instance attribute for source.
  - `channel` (`Any`): Instance attribute for channel.
  - `bound_context` (`Dict[...]`): Instance attribute for bound_context.
  - `_writer` (`Any`): Instance attribute for _writer.

- **Methods**:
  - `__init__(server_id, source, channel, bound) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `get_instance`.
  - `isEnabledFor(level) -> bool`: Check if the given numeric level is enabled based on current CONFIG.
  - `bind(**context) -> LoggerAdapter`: Return a new LoggerAdapter with merged context, similar to structlog.bind.
  - `_emit(level, message, exception, **event_fields) -> None`: Compose structured record, enqueue NDJSON line, and render to console as single-line text.
  - `_format_console_line(record) -> str`: Create enhanced console representation with simplified timestamp and optional emoji.
  - `_colorize_line(record, line) -> str`: Apply ANSI color codes to different parts of the log line for better readability.
  - `info(message, *args, **event_fields) -> None`: Emit an INFO event.
  - `warning(message, *args, **event_fields) -> None`: Emit a WARNING event.
  - `error(message, *args, **event_fields) -> None`: Emit an ERROR event.
  - `debug(message, *args, **event_fields) -> None`: Emit a DEBUG event.
  - `exception(message, *args, **event_fields) -> None`: Log an ERROR-level event with the current exception traceback.

### `InterceptHandler`
Logging.Handler that redirects stdlib logging records into our structured logger.

It routes messages to get_logger(server_id='Bot', source=record.name) while avoiding
recursion from this module or loguru internals.

- **Methods**:
  - `emit(record) -> None`: Handles the `emit` functionality. Internally, it interacts with methods like `update` and `upper`.

## Functions

### `_check_color_support() -> bool`
Enhanced check for terminal color support including Windows.

### `load_config_from_settings() -> None`
Load logging configuration from addons.settings.base_config and merge with defaults.

### `init_loguru_console() -> None`
Initialize or reconfigure the loguru console sink based on current CONFIG.

### `get_logger(server_id, source, channel) -> LoggerAdapter`
Factory returning a bindable logger-like object for a given server_id.

### `configure_std_logging() -> None`
Configure the standard library logging to route through InterceptHandler and apply third-party levels.
