# File: `cogs/memory/db/connection.py`

## Overview
Database connection manager for the memory cog.

Handles SQLite connection lifecycle, thread-safe access, and error reporting.

## Classes

### `DatabaseConnection`
Manage SQLite connections per-thread and provide thread-safe access.

- **Attributes**:
  - `db_path` (`Any`): Attribute holding db_path data.
  - `bot` (`Any`): Attribute holding bot data.
  - `_loop` (`Any`): Attribute holding _loop data.
  - `logger` (`Any`): Attribute holding logger data.
  - `_lock` (`Any`): Attribute holding _lock data.
  - `_connections` (`Dict[Tuple[int, sqlite3.Connection]]`): Attribute holding _connections data.

- **Methods**:
  - `__init__(db_path: Union[Tuple[str, Path]], bot: Optional[PigPig]) -> Any`: Initialize connection manager.
  - `_report_error_threadsafe(exc: Exception, ctx: str) -> None`: Report errors in a thread-safe manner to the async error reporter.
  - `get_connection() -> Any`: Context manager that yields a sqlite3.Connection bound to the current thread.
  - `close_connections() -> None`: Close all managed SQLite connections.

## Functions

No top-level functions defined.
