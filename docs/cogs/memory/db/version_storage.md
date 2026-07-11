# File: `cogs/memory/db/version_storage.py`

## Overview
This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `version_storage.py`, providing vital integrations within the PigPig bot ecosystem.
Per-guild version tracking storage.

Stores which bot version each guild has already seen, so the
version-announcement feature fires exactly once per version per guild.

## Classes

### `GuildVersionStorage`
SQLite-backed store for per-guild seen-version tracking.

Uses an isolated SQLite connection so it works regardless of whether
the memory sub-system is enabled.

- **Attributes**:
  - `db_path` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(db_path: Union[Tuple]) -> None`: Initialize and ensure the required table exists.
  - `_open_connection() -> sqlite3.Connection`: Open (or reuse) the SQLite connection.
  - `_ensure_table() -> None`: Create the guild_version_seen table if it does not exist.
  - `get_seen_version(guild_id: str) -> Optional[str]`: Return the last seen bot version for a guild, or None if not recorded.
  - `set_seen_version(guild_id: str, version: str) -> None`: Record that guild_id has seen the given bot version.
