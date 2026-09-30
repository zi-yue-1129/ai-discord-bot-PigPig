# File: `addons/logging.py`

## Overview
This file is part of utility modules and configurations and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `addons/logging.py`.

## Classes

### `LogRecord`
Structured log record following plan.md schema.

- **Attributes**:
  - `timestamp` (`str`): Attribute timestamp
  - `level` (`str`): Attribute level
  - `source` (`str`): Attribute source
  - `server_id` (`str`): Attribute server_id
  - `channel_or_file` (`str`): Attribute channel_or_file
  - `user_id` (`str`): Attribute user_id
  - `action` (`str`): Attribute action
  - `message` (`str`): Attribute message
  - `trace_id` (`Optional[str]`): Attribute trace_id
  - `extra` (`Dict[str, Any]`): Attribute extra

- **Methods**:
  - `to_json_line(self) -> str`: Serialize record to a single NDJSON line.

### `BackgroundWriter`
Background single-thread writer that batches NDJSON records and writes per-level files.

- **Attributes**:
  - `_instance` (`Any`): Attribute _instance
  - `_instance_lock` (`Any`): Attribute _instance_lock
  - `batch_size` (`int`): Instance attribute batch_size
  - `flush_interval` (`float`): Instance attribute flush_interval
  - `queue_maxsize` (`int`): Instance attribute queue_maxsize
  - `_queue` (`'Queue[Dict[str, Any]]'`): Instance attribute _queue
  - `_thread` (`Any`): Instance attribute _thread
  - `_stop_event` (`Any`): Instance attribute _stop_event
  - `_metrics` (`Any`): Instance attribute _metrics

- **Methods**:
  - `get_instance(cls) -> 'BackgroundWriter'`: Method get_instance.
  - `enqueue(self, server_id, level, json_line, timestamp_iso) -> None`: Attempt to enqueue a log event non-blocking. On full queue, drop and report.
  - `_report_error_async(self, exc, context) -> None`: Report errors through func.report_error if available, fallback to printing.
  - `stop(self, timeout) -> None`: Signal worker to stop and flush remaining items.
  - `_worker(self) -> None`: Worker loop: collect batches and perform grouped writes per server/date/level.

### `LoggerAdapter`
Logger-like object exposing bind(...) and level methods (info/warning/error/debug).  This provides a minimal structlog-like API for bindable context while delegating actual output to BackgroundWriter and loguru console renderer.

- **Attributes**:
  - `_COLORS` (`Any`): Attribute _COLORS
  - `_LEVEL_EMOJI` (`Any`): Attribute _LEVEL_EMOJI
  - `DEBUG` (`Any`): Attribute DEBUG
  - `INFO` (`Any`): Attribute INFO
  - `WARNING` (`Any`): Attribute WARNING
  - `ERROR` (`Any`): Attribute ERROR
  - `CRITICAL` (`Any`): Attribute CRITICAL
  - `_LEVEL_NAME_TO_INT` (`Any`): Attribute _LEVEL_NAME_TO_INT
  - `server_id` (`Any`): Instance attribute server_id
  - `source` (`Any`): Instance attribute source
  - `channel` (`Any`): Instance attribute channel
  - `bound_context` (`Dict[str, Any]`): Instance attribute bound_context
  - `_writer` (`Any`): Instance attribute _writer

- **Methods**:
  - `isEnabledFor(self, level) -> bool`: Check if the given numeric level is enabled based on current CONFIG.
  - `bind(self, **context) -> 'LoggerAdapter'`: Return a new LoggerAdapter with merged context, similar to structlog.bind.
  - `_emit(self, level, message, exception, **event_fields) -> None`: Compose structured record, enqueue NDJSON line, and render to console as single-line text.
  - `_format_console_line(self, record) -> str`: Create enhanced console representation with simplified timestamp and optional emoji.
  - `_colorize_line(self, record, line) -> str`: Apply ANSI color codes to different parts of the log line for better readability.
  - `info(self, message, *args, **event_fields) -> None`: Emit an INFO event.  Accept calling styles: - logger.info("text %s", "arg") (printf-style) - logger.info("text", user_id=...) (positional message) - logger.info(user_id=..., message="text") (message in kwargs)
  - `warning(self, message, *args, **event_fields) -> None`: Emit a WARNING event.
  - `error(self, message, *args, **event_fields) -> None`: Emit an ERROR event.
  - `debug(self, message, *args, **event_fields) -> None`: Emit a DEBUG event.
  - `exception(self, message, *args, **event_fields) -> None`: Log an ERROR-level event with the current exception traceback.

### `InterceptHandler`
Logging.Handler that redirects stdlib logging records into our structured logger.  It routes messages to get_logger(server_id='Bot', source=record.name) while avoiding recursion from this module or loguru internals.

- **Attributes**:
  - None

- **Methods**:
  - `emit(self, record) -> None`: Method emit.

## Functions

### `_check_color_support() -> bool`
Enhanced check for terminal color support including Windows.

### `load_config_from_settings() -> None`
Load logging configuration from addons.settings.base_config and merge with defaults.  This function should be called by addons.settings after it successfully constructs BaseConfig from CONFIG_ROOT so user configuration is applied.

### `init_loguru_console() -> None`
Initialize or reconfigure the loguru console sink based on current CONFIG.  Call this after load_config_from_settings() so the console format and color options come from the user's configuration.

### `get_logger(server_id, source, channel) -> LoggerAdapter`
Factory returning a bindable logger-like object for a given server_id.  server_id: string or int representing server/guild id source: "server" | "system" | "external" channel: optional channel or file name for context

### `configure_std_logging() -> None`
Configure the standard library logging to route through InterceptHandler and apply third-party levels.  This function: - Removes existing handlers from the root logger. - Adds InterceptHandler to capture stdlib logging and funnel it into our structured logger. - Attempts to remove non-root handlers to avoid duplicate/unstructured outputs. - Applies per-logger level overrides from settings.base_config.logging['third_party_levels'] if present.

