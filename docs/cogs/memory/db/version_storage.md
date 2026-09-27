# File: `cogs/memory/db/version_storage.py`

## Overview
Per-guild version tracking storage.

Stores which bot version each guild has already seen, so the
version-announcement feature fires exactly once per version per guild.

## Classes

### `GuildVersionStorage`
SQLite-backed store for per-guild seen-version tracking.

Uses an isolated SQLite connection so it works regardless of whether
the memory sub-system is enabled.

- **Attributes**:
  - `db_path` (`Any`): Instance attribute for db_path.
  - `_conn` (`Optional[...]`): Instance attribute for _conn.

- **Methods**:
  - `__init__(db_path) -> None`: Initialize and ensure the required table exists.
  - `_open_connection() -> sqlite3.Connection`: Open (or reuse) the SQLite connection.
  - `_ensure_table() -> None`: Create the guild_version_seen table if it does not exist.
  - `get_seen_version(guild_id) -> Optional[...]`: Return the last seen bot version for a guild, or None if not recorded.
  - `set_seen_version(guild_id, version) -> None`: Record that guild_id has seen the given bot version.
