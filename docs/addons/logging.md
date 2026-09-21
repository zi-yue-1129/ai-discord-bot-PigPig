# File: `addons/logging.py`

## Overview
This file is part of the addons subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `LogRecord`
Structured log record following plan.md schema.

- **Attributes**:
  - `timestamp` (`str`): Attribute holding timestamp data.
  - `level` (`str`): Attribute holding level data.
  - `source` (`str`): Attribute holding source data.
  - `server_id` (`str`): Attribute holding server_id data.
  - `channel_or_file` (`str`): Attribute holding channel_or_file data.
  - `user_id` (`str`): Attribute holding user_id data.
  - `action` (`str`): Attribute holding action data.
  - `message` (`str`): Attribute holding message data.
  - `trace_id` (`Optional[str]`): Attribute holding trace_id data.
  - `extra` (`Dict[Tuple[str, Any]]`): Attribute holding extra data.

- **Methods**:
  - `to_json_line() -> str`: Serialize record to a single NDJSON line.

### `BackgroundWriter`
Background single-thread writer that batches NDJSON records and writes per-level files.

- **Attributes**:
  - `batch_size` (`int`): Attribute holding batch_size data.
  - `flush_interval` (`float`): Attribute holding flush_interval data.
  - `queue_maxsize` (`int`): Attribute holding queue_maxsize data.
  - `_queue` (`Queue[Dict[str, Any]]`): Attribute holding _queue data.
  - `_thread` (`Any`): Attribute holding _thread data.
  - `_stop_event` (`Any`): Attribute holding _stop_event data.
  - `_metrics` (`Any`): Attribute holding _metrics data.

- **Methods**:
  - `__init__() -> Any`: Executes __init__ logic.
  - `get_instance(cls) -> BackgroundWriter`: Executes get_instance logic.
  - `enqueue(server_id: str, level: str, json_line: str, timestamp_iso: str) -> None`: Attempt to enqueue a log event non-blocking. On full queue, drop and report.
  - `_report_error_async(exc: Exception, context: str) -> None`: Report errors through func.report_error if available, fallback to printing.
  - `stop(timeout: float) -> None`: Signal worker to stop and flush remaining items.
  - `_worker() -> None`: Worker loop: collect batches and perform grouped writes per server/date/level.

### `LoggerAdapter`
Logger-like object exposing bind(...) and level methods (info/warning/error/debug).

This provides a minimal structlog-like API for bindable context while delegating
actual output to BackgroundWriter and loguru console renderer.

- **Attributes**:
  - `server_id` (`Any`): Attribute holding server_id data.
  - `source` (`Any`): Attribute holding source data.
  - `channel` (`Any`): Attribute holding channel data.
  - `bound_context` (`Dict[Tuple[str, Any]]`): Attribute holding bound_context data.
  - `_writer` (`Any`): Attribute holding _writer data.

- **Methods**:
  - `__init__(server_id: str, source: str, channel: Optional[str], bound: Optional[Dict[Tuple[str, Any]]]) -> Any`: Executes __init__ logic.
  - `isEnabledFor(level: int) -> bool`: Check if the given numeric level is enabled based on current CONFIG.
  - `bind(**context) -> LoggerAdapter`: Return a new LoggerAdapter with merged context, similar to structlog.bind.
  - `_emit(level: str, message: str, exception: Optional[BaseException], **event_fields) -> None`: Compose structured record, enqueue NDJSON line, and render to console as single-line text.
  - `_format_console_line(record: LogRecord) -> str`: Create enhanced console representation with simplified timestamp and optional emoji.
  - `_colorize_line(record: LogRecord, line: str) -> str`: Apply ANSI color codes to different parts of the log line for better readability.
  - `info(message: Optional[str], *args, **event_fields, exception: Optional[BaseException]) -> None`: Emit an INFO event.
  - `warning(message: Optional[str], *args, **event_fields, exception: Optional[BaseException]) -> None`: Emit a WARNING event.
  - `error(message: Optional[str], *args, **event_fields, exception: Optional[BaseException]) -> None`: Emit an ERROR event.
  - `debug(message: Optional[str], *args, **event_fields, exception: Optional[BaseException]) -> None`: Emit a DEBUG event.
  - `exception(message: Optional[str], *args, **event_fields) -> None`: Log an ERROR-level event with the current exception traceback.

### `InterceptHandler`
Logging.Handler that redirects stdlib logging records into our structured logger.

It routes messages to get_logger(server_id='Bot', source=record.name) while avoiding
recursion from this module or loguru internals.

- **Attributes**:
  - None specified.

- **Methods**:
  - `emit(record: logging.LogRecord) -> None`: Executes emit logic.

## Functions

### `_check_color_support() -> bool`
Enhanced check for terminal color support including Windows.

### `load_config_from_settings() -> None`
Load logging configuration from addons.settings.base_config and merge with defaults.

This function should be called by addons.settings after it successfully
constructs BaseConfig from CONFIG_ROOT so user configuration is applied.

### `init_loguru_console() -> None`
Initialize or reconfigure the loguru console sink based on current CONFIG.

Call this after load_config_from_settings() so the console format and color
options come from the user's configuration.

### `get_logger(server_id: Any, source: str, channel: Optional[str]) -> LoggerAdapter`
Factory returning a bindable logger-like object for a given server_id.

server_id: string or int representing server/guild id
source: "server" | "system" | "external"
channel: optional channel or file name for context

### `configure_std_logging() -> None`
Configure the standard library logging to route through InterceptHandler and apply third-party levels.

This function:
- Removes existing handlers from the root logger.
- Adds InterceptHandler to capture stdlib logging and funnel it into our structured logger.
- Attempts to remove non-root handlers to avoid duplicate/unstructured outputs.
- Applies per-logger level overrides from settings.base_config.logging['third_party_levels'] if present.
