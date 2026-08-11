# File: `cogs/memory/db/procedural_storage.py`

## Overview
ProceduralStorage: handles users table and configuration storage.

This module extracts the procedural (user) related SQL logic from the previous
sqlite_storage implementation so responsibilities are separated.
All error reporting uses func.report_error per project rules.

## Classes

### `ProceduralStorage`
Handles users table and config storage.

- **Attributes**:
  - `db` (`Any`): Instance attribute managing db.
  - `_cache_size_limit` (`Any`): Instance attribute managing _cache_size_limit.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `get_user_info(discord_id) -> Optional[UserInfo]`: Executes get_user_info operation.
  - `get_users_info(discord_ids) -> Dict[Tuple[str, UserInfo]]`: Fetch multiple users efficiently using a single SQL query.
  - `update_user_data(discord_id, discord_name, procedural_memory, user_background, display_names, nickname) -> bool`: Executes update_user_data operation.
  - `delete_user_data(discord_id) -> bool`: Executes delete_user_data operation.
  - `update_user_activity(discord_id, discord_name, nickname) -> bool`: Executes update_user_activity operation.
  - `get_all_users(limit, offset) -> List[UserInfo]`: Return all users ordered by creation date (newest first).
  - `get_users_count() -> int`: Return total number of users in the database.
  - `get_config(key) -> Optional[str]`: Executes get_config operation.
  - `set_config(key, value) -> None`: Executes set_config operation.
