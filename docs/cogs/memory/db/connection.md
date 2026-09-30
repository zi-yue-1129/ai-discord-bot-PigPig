# File: `cogs/memory/db/connection.py`

## Overview
Database connection manager for the memory cog.

Handles SQLite connection lifecycle, thread-safe access, and error reporting.

## Classes

### `DatabaseConnection`
Manage SQLite connections per-thread and provide thread-safe access.

- **Attributes**:
  - `db_path` (`Any`): Instance attribute db_path
  - `bot` (`Any`): Instance attribute bot
  - `_loop` (`Any`): Instance attribute _loop
  - `logger` (`Any`): Instance attribute logger
  - `_lock` (`Any`): Instance attribute _lock
  - `_connections` (`Dict[int, sqlite3.Connection]`): Instance attribute _connections

- **Methods**:
  - `_report_error_threadsafe(self, exc, ctx) -> None`: Report errors in a thread-safe manner to the async error reporter.  If an event loop is available, submit func.report_error via asyncio.run_coroutine_threadsafe; otherwise fall back to logger.
  - `get_connection(self) -> Any`: Context manager that yields a sqlite3.Connection bound to the current thread.
  - `close_connections(self) -> None`: Close all managed SQLite connections.

## Functions

None
