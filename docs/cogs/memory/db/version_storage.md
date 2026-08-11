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
  - `db_path` (`Any`): Instance attribute managing db_path.

- **Methods**:
  - `get_seen_version(guild_id) -> Optional[str]`: Return the last seen bot version for a guild, or None if not recorded.  Args:     guild_id: Discord guild ID as a string.  Returns:     Version string (e.g. "v3.2.0") or None.
  - `set_seen_version(guild_id, version) -> None`: Record that guild_id has seen the given bot version.  Args:     guild_id: Discord guild ID as a string.     version: Bot version string (e.g. "v3.2.0").  Raises:     sqlite3.Error: On database write failure.
