# File: `addons/logging.py`

## Overview
Core file handling responsibilities within the `addons` subsystem.

## Classes

### `LogRecord`
Structured log record following plan.md schema.

- **Attributes**:
  - `timestamp` (`str`): Class attribute
  - `level` (`str`): Class attribute
  - `source` (`str`): Class attribute
  - `server_id` (`str`): Class attribute
  - `channel_or_file` (`str`): Class attribute
  - `user_id` (`str`): Class attribute
  - `action` (`str`): Class attribute
  - `message` (`str`): Class attribute
  - `trace_id` (`Optional[str]`): Class attribute
  - `extra` (`Dict[Tuple[str, Any]]`): Class attribute

- **Methods**:
  - `to_json_line() -> str`: Serialize record to a single NDJSON line.

### `BackgroundWriter`
Background single-thread writer that batches NDJSON records and writes per-level files.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__() -> Any`: No description provided.
  - `get_instance(cls) -> str`: No description provided.
  - `enqueue(server_id: str, level: str, json_line: str, timestamp_iso: str) -> None`: Attempt to enqueue a log event non-blocking. On full queue, drop and report.
  - `_report_error_async(exc: Exception, context: str) -> None`: Report errors through func.report_error if available, fallback to printing.
  - `stop(timeout: float) -> None`: Signal worker to stop and flush remaining items.
  - `_worker() -> None`: Worker loop: collect batches and perform grouped writes per server/date/level.

### `LoggerAdapter`
Logger-like object exposing bind(...) and level methods (info/warning/error/debug).

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(server_id: str, source: str, channel: Optional[str], bound: Optional[Dict[Tuple[str, Any]]]) -> Any`: No description provided.
  - `isEnabledFor(level: int) -> bool`: Check if the given numeric level is enabled based on current CONFIG.
  - `bind(**context: Any) -> str`: Return a new LoggerAdapter with merged context, similar to structlog.bind.
  - `_emit(level: str, message: str, exception: Optional[BaseException], **event_fields: Any) -> None`: Compose structured record, enqueue NDJSON line, and render to console as single-line text.
  - `_format_console_line(record: LogRecord) -> str`: Create enhanced console representation with simplified timestamp and optional emoji.
  - `_colorize_line(record: LogRecord, line: str) -> str`: Apply ANSI color codes to different parts of the log line for better readability.
  - `info(message: Optional[str], *args: Any, exception: Optional[BaseException], **event_fields: Any) -> None`: Emit an INFO event.
  - `warning(message: Optional[str], *args: Any, exception: Optional[BaseException], **event_fields: Any) -> None`: Emit a WARNING event.
  - `error(message: Optional[str], *args: Any, exception: Optional[BaseException], **event_fields: Any) -> None`: Emit an ERROR event.
  - `debug(message: Optional[str], *args: Any, exception: Optional[BaseException], **event_fields: Any) -> None`: Emit a DEBUG event.
  - `exception(message: Optional[str], *args: Any, **event_fields: Any) -> None`: Log an ERROR-level event with the current exception traceback.

### `InterceptHandler`
Logging.Handler that redirects stdlib logging records into our structured logger.

- **Attributes**:
  - None specified.

- **Methods**:
  - `emit(record: logging.LogRecord) -> None`: No description provided.

## Functions

### `_check_color_support() -> bool`
Enhanced check for terminal color support including Windows.

### `load_config_from_settings() -> None`
Load logging configuration from addons.settings.base_config and merge with defaults.

### `init_loguru_console() -> None`
Initialize or reconfigure the loguru console sink based on current CONFIG.

### `get_logger(server_id: Any, source: str, channel: Optional[str]) -> LoggerAdapter`
Factory returning a bindable logger-like object for a given server_id.

### `configure_std_logging() -> None`
Configure the standard library logging to route through InterceptHandler and apply third-party levels.

