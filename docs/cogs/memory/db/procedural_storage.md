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
  - `db` (`Any`): Attribute holding db data.
  - `_user_cache` (`Dict[Tuple[str, UserInfo]]`): Attribute holding _user_cache data.
  - `_cache_size_limit` (`Any`): Attribute holding _cache_size_limit data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(db: DatabaseConnection) -> None`: Executes __init__ logic.
  - `get_user_info(discord_id: str) -> Optional[UserInfo]`: Executes get_user_info logic.
  - `_get_user_info_sync(discord_id: str) -> Optional[UserInfo]`: Executes _get_user_info_sync logic.
  - `get_users_info(discord_ids: List[str]) -> Dict[Tuple[str, UserInfo]]`: Fetch multiple users efficiently using a single SQL query.
  - `update_user_data(discord_id: str, discord_name: str, procedural_memory: Optional[str], user_background: Optional[str], display_names: Optional[List[str]], nickname: Optional[str]) -> bool`: Executes update_user_data logic.
  - `_update_user_data_sync(discord_id: str, discord_name: str, procedural_memory: Optional[str], user_background: Optional[str], display_names: Optional[List[str]], nickname: Optional[str]) -> bool`: Executes _update_user_data_sync logic.
  - `delete_user_data(discord_id: str) -> bool`: Executes delete_user_data logic.
  - `_delete_user_data_sync(discord_id: str) -> bool`: Executes _delete_user_data_sync logic.
  - `update_user_activity(discord_id: str, discord_name: str, nickname: Optional[str]) -> bool`: Executes update_user_activity logic.
  - `_update_user_activity_sync(discord_id: str, discord_name: str, nickname: Optional[str]) -> bool`: Executes _update_user_activity_sync logic.
  - `get_all_users(limit: int, offset: int) -> List[UserInfo]`: Return all users ordered by creation date (newest first).
  - `_get_all_users_sync(limit: int, offset: int) -> List[UserInfo]`: Executes _get_all_users_sync logic.
  - `get_users_count() -> int`: Return total number of users in the database.
  - `_get_users_count_sync() -> int`: Executes _get_users_count_sync logic.
  - `get_config(key: str) -> Optional[str]`: Executes get_config logic.
  - `_get_config_sync(key: str) -> Optional[str]`: Executes _get_config_sync logic.
  - `set_config(key: str, value: str) -> None`: Executes set_config logic.
  - `_set_config_sync(key: str, value: str) -> None`: Executes _set_config_sync logic.
  - `_update_cache(user_id: str, user_info: UserInfo) -> None`: Executes _update_cache logic.

## Functions

No top-level functions defined.
