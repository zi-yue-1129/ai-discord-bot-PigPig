# File: `cogs/memory/db/connection.py`

## Overview
Database connection manager for the memory cog.

Handles SQLite connection lifecycle, thread-safe access, and error reporting.

## Classes

### `DatabaseConnection`
Manage SQLite connections per-thread and provide thread-safe access.

- **Attributes**:
  - `db_path` (`Any`): Instance attribute for db_path.
  - `bot` (`Any`): Instance attribute for bot.
  - `_loop` (`Any`): Instance attribute for _loop.
  - `logger` (`Any`): Instance attribute for logger.
  - `_lock` (`Any`): Instance attribute for _lock.
  - `_connections` (`Dict[...]`): Instance attribute for _connections.

- **Methods**:
  - `__init__(db_path, bot) -> Any`: Initialize connection manager.
  - `_report_error_threadsafe(exc, ctx) -> None`: Report errors in a thread-safe manner to the async error reporter.
  - `get_connection() -> Any`: Context manager that yields a sqlite3.Connection bound to the current thread.
  - `close_connections() -> None`: Close all managed SQLite connections.
