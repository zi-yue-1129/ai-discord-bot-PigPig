# File: `addons/logging.py`

## Overview
The `addons/logging.py` module provides a high-performance, structured logging system. It is designed for multi-guild environments, ensuring that logs are categorized by server ID and stored in a machine-readable NDJSON format while maintaining a beautiful, colorized console output.

This file belongs to the Addons Subsystem. Its core responsibility is to handle logic related to `logging.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `LogRecord`
Structured log record following plan.md schema.

- **Attributes**:
  - `timestamp` (`str`): Property holding the timestamp state.
  - `level` (`str`): Property holding the level state.
  - `source` (`str`): Property holding the source state.
  - `server_id` (`str`): Property holding the server_id state.
  - `channel_or_file` (`str`): Property holding the channel_or_file state.
  - `user_id` (`str`): Property holding the user_id state.
  - `action` (`str`): Property holding the action state.
  - `message` (`str`): Property holding the message state.
  - `trace_id` (`Optional[str]`): Property holding the trace_id state.
  - `extra` (`Dict[Tuple]`): Property holding the extra state.

- **Methods**:
  - `to_json_line() -> str`: Serialize record to a single NDJSON line.

### `BackgroundWriter`
Background single-thread writer that batches NDJSON records and writes per-level files.

- **Attributes**:
  - `_thread` (`Any`): Internal instance state.
  - `_stop_event` (`Any`): Internal instance state.
  - `_metrics` (`Any`): Internal instance state.

- **Methods**:
  - `__init__() -> Any`: Performs internal processing logic.
  - `get_instance(cls: Any) -> BackgroundWriter`: Performs internal processing logic.
  - `enqueue(server_id: str, level: str, json_line: str, timestamp_iso: str) -> None`: Attempt to enqueue a log event non-blocking. On full queue, drop and report.
  - `_report_error_async(exc: Exception, context: str) -> None`: Report errors through func.report_error if available, fallback to printing.
  - `stop(timeout: float) -> None`: Signal worker to stop and flush remaining items.
  - `_worker() -> None`: Worker loop: collect batches and perform grouped writes per server/date/level.

### `LoggerAdapter`
Logger-like object exposing bind(...) and level methods (info/warning/error/debug).

This provides a minimal structlog-like API for bindable context while delegating
actual output to BackgroundWriter and loguru console renderer.

- **Attributes**:
  - `server_id` (`Any`): Internal instance state.
  - `source` (`Any`): Internal instance state.
  - `channel` (`Any`): Internal instance state.
  - `_writer` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(server_id: str, source: str, channel: Optional[str], bound: Optional[Dict[Tuple]]) -> Any`: Performs internal processing logic.
  - `isEnabledFor(level: int) -> bool`: Check if the given numeric level is enabled based on current CONFIG.
  - `bind() -> LoggerAdapter`: Return a new LoggerAdapter with merged context, similar to structlog.bind.
  - `_emit(level: str, message: str, exception: Optional[BaseException]) -> None`: Compose structured record, enqueue NDJSON line, and render to console as single-line text.
  - `_format_console_line(record: LogRecord) -> str`: Create enhanced console representation with simplified timestamp and optional emoji.
  - `_colorize_line(record: LogRecord, line: str) -> str`: Apply ANSI color codes to different parts of the log line for better readability.
  - `info(message: Optional[str]) -> None`: Emit an INFO event.
  - `warning(message: Optional[str]) -> None`: Emit a WARNING event.
  - `error(message: Optional[str]) -> None`: Emit an ERROR event.
  - `debug(message: Optional[str]) -> None`: Emit a DEBUG event.
  - `exception(message: Optional[str]) -> None`: Log an ERROR-level event with the current exception traceback.

### `InterceptHandler`
Logging.Handler that redirects stdlib logging records into our structured logger.

It routes messages to get_logger(server_id='Bot', source=record.name) while avoiding
recursion from this module or loguru internals.

- **Methods**:
  - `emit(record: logging.LogRecord) -> None`: Performs internal processing logic.

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
