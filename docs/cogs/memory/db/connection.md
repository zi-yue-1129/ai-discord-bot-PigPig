# File: `cogs/memory/db/connection.py`

## Overview
Database connection manager for the memory cog.

## Classes

### `DatabaseConnection`
Manage SQLite connections per-thread and provide thread-safe access.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(db_path: Union[Tuple[str, Path]], bot: Optional[str]) -> Any`: Initialize connection manager.
  - `_report_error_threadsafe(exc: Exception, ctx: str) -> None`: Report errors in a thread-safe manner to the async error reporter.
  - `get_connection() -> Any`: Context manager that yields a sqlite3.Connection bound to the current thread.
  - `close_connections() -> None`: Close all managed SQLite connections.

## Functions

No module-level functions defined in this file.
