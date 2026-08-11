# File: `cogs/memory/db/connection.py`

## Overview
Database connection manager for the memory cog.

Handles SQLite connection lifecycle, thread-safe access, and error reporting.

## Classes

### `DatabaseConnection`
Manage SQLite connections per-thread and provide thread-safe access.

- **Attributes**:
  - `db_path` (`Any`): Instance attribute managing db_path.
  - `bot` (`Any`): Instance attribute managing bot.
  - `_loop` (`Any`): Instance attribute managing _loop.
  - `logger` (`Any`): Instance attribute managing logger.
  - `_lock` (`Any`): Instance attribute managing _lock.

- **Methods**:
  - `get_connection() -> Any`: Context manager that yields a sqlite3.Connection bound to the current thread.
  - `close_connections() -> None`: Close all managed SQLite connections.
