# File: `addons/logging.py`

## Overview
The `addons/logging.py` module provides a high-performance, structured logging system. It is designed for multi-guild environments, ensuring that logs are categorized by server ID and stored in a machine-readable NDJSON format while maintaining a beautiful, colorized console output.

## Classes

### `LogRecord`
Structured log record following plan.md schema.

- **Attributes**:
  - `timestamp` (`str`): Stores data related to timestamp.
  - `level` (`str`): Stores data related to level.
  - `source` (`str`): Stores data related to source.
  - `server_id` (`str`): Stores data related to server_id.
  - `channel_or_file` (`str`): Stores data related to channel_or_file.
  - `user_id` (`str`): Stores data related to user_id.
  - `action` (`str`): Stores data related to action.
  - `message` (`str`): Stores data related to message.
  - `trace_id` (`Optional[str]`): Stores data related to trace_id.
  - `extra` (`Dict[Tuple[str, Any]]`): Stores data related to extra.

- **Methods**:
  - `to_json_line() -> str`: Serialize record to a single NDJSON line.

### `BackgroundWriter`
Background single-thread writer that batches NDJSON records and writes per-level files.

- **Attributes**:
  - `_thread` (`Any`): Instance attribute managing _thread.
  - `_stop_event` (`Any`): Instance attribute managing _stop_event.
  - `_metrics` (`Any`): Instance attribute managing _metrics.

- **Methods**:
  - `get_instance(cls) -> BackgroundWriter`: Executes logic for get_instance.
  - `enqueue(server_id, level, json_line, timestamp_iso) -> None`: Attempt to enqueue a log event non-blocking. On full queue, drop and report.
  - `stop(timeout) -> None`: Signal worker to stop and flush remaining items.

### `LoggerAdapter`
Logger-like object exposing bind(...) and level methods (info/warning/error/debug).

This provides a minimal structlog-like API for bindable context while delegating
actual output to BackgroundWriter and loguru console renderer.

- **Attributes**:
  - `server_id` (`Any`): Instance attribute managing server_id.
  - `source` (`Any`): Instance attribute managing source.
  - `channel` (`Any`): Instance attribute managing channel.
  - `_writer` (`Any`): Instance attribute managing _writer.

- **Methods**:
  - `isEnabledFor(level) -> bool`: Check if the given numeric level is enabled based on current CONFIG.
  - `bind(**context) -> LoggerAdapter`: Return a new LoggerAdapter with merged context, similar to structlog.bind.
  - `info(message, *args, **event_fields) -> None`: Emit an INFO event.  Accept calling styles: - logger.info("text %s", "arg") (printf-style) - logger.info("text", user_id=...) (positional message) - logger.info(user_id=..., message="text") (message in kwargs)
  - `warning(message, *args, **event_fields) -> None`: Emit a WARNING event.
  - `error(message, *args, **event_fields) -> None`: Emit an ERROR event.
  - `debug(message, *args, **event_fields) -> None`: Emit a DEBUG event.
  - `exception(message, *args, **event_fields) -> None`: Log an ERROR-level event with the current exception traceback.

### `InterceptHandler`
Logging.Handler that redirects stdlib logging records into our structured logger.

It routes messages to get_logger(server_id='Bot', source=record.name) while avoiding
recursion from this module or loguru internals.

- **Methods**:
  - `emit(record) -> None`: Executes logic for emit.

## Functions

### `load_config_from_settings() -> None`
Load logging configuration from addons.settings.base_config and merge with defaults.

This function should be called by addons.settings after it successfully
constructs BaseConfig from CONFIG_ROOT so user configuration is applied.

### `init_loguru_console() -> None`
Initialize or reconfigure the loguru console sink based on current CONFIG.

Call this after load_config_from_settings() so the console format and color
options come from the user's configuration.

### `get_logger(server_id, source, channel) -> LoggerAdapter`
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

