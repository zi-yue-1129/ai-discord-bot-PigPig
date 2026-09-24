# File: `cogs/memory/db/version_storage.py`

## Overview
Per-guild version tracking storage.

## Classes

### `GuildVersionStorage`
SQLite-backed store for per-guild seen-version tracking.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(db_path: Union[Tuple[str, Path]]) -> None`: Initialize and ensure the required table exists.
  - `_open_connection() -> sqlite3.Connection`: Open (or reuse) the SQLite connection.
  - `_ensure_table() -> None`: Create the guild_version_seen table if it does not exist.
  - `get_seen_version(guild_id: str) -> Optional[str]`: Return the last seen bot version for a guild, or None if not recorded.
  - `set_seen_version(guild_id: str, version: str) -> None`: Record that guild_id has seen the given bot version.

## Functions

No module-level functions defined in this file.
