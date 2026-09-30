# File: `cogs/memory/db/version_storage.py`

## Overview
Per-guild version tracking storage.

Stores which bot version each guild has already seen, so the
version-announcement feature fires exactly once per version per guild.

## Classes

### `GuildVersionStorage`
SQLite-backed store for per-guild seen-version tracking.  Uses an isolated SQLite connection so it works regardless of whether the memory sub-system is enabled.

- **Attributes**:
  - `db_path` (`Any`): Instance attribute db_path
  - `_conn` (`Optional[sqlite3.Connection]`): Instance attribute _conn

- **Methods**:
  - `_open_connection(self) -> sqlite3.Connection`: Open (or reuse) the SQLite connection.  Returns:     An open sqlite3.Connection.
  - `_ensure_table(self) -> None`: Create the guild_version_seen table if it does not exist.
  - `get_seen_version(self, guild_id) -> Optional[str]`: Return the last seen bot version for a guild, or None if not recorded.  Args:     guild_id: Discord guild ID as a string.  Returns:     Version string (e.g. "v3.2.0") or None.
  - `set_seen_version(self, guild_id, version) -> None`: Record that guild_id has seen the given bot version.  Args:     guild_id: Discord guild ID as a string.     version: Bot version string (e.g. "v3.2.0").  Raises:     sqlite3.Error: On database write failure.

## Functions

None
