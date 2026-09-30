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
  - `db` (`Any`): Instance attribute db
  - `_user_cache` (`Dict[str, UserInfo]`): Instance attribute _user_cache
  - `_cache_size_limit` (`Any`): Instance attribute _cache_size_limit
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `get_user_info(self, discord_id) -> Optional[UserInfo]`: Method get_user_info.
  - `_get_user_info_sync(self, discord_id) -> Optional[UserInfo]`: Method _get_user_info_sync.
  - `get_users_info(self, discord_ids) -> Dict[str, UserInfo]`: Fetch multiple users efficiently using a single SQL query.
  - `update_user_data(self, discord_id, discord_name, procedural_memory, user_background, display_names, nickname) -> bool`: Method update_user_data.
  - `_update_user_data_sync(self, discord_id, discord_name, procedural_memory, user_background, display_names, nickname) -> bool`: Method _update_user_data_sync.
  - `delete_user_data(self, discord_id) -> bool`: Method delete_user_data.
  - `_delete_user_data_sync(self, discord_id) -> bool`: Method _delete_user_data_sync.
  - `update_user_activity(self, discord_id, discord_name, nickname) -> bool`: Method update_user_activity.
  - `_update_user_activity_sync(self, discord_id, discord_name, nickname) -> bool`: Method _update_user_activity_sync.
  - `get_all_users(self, limit, offset) -> List[UserInfo]`: Return all users ordered by creation date (newest first).
  - `_get_all_users_sync(self, limit, offset) -> List[UserInfo]`: Method _get_all_users_sync.
  - `get_users_count(self) -> int`: Return total number of users in the database.
  - `_get_users_count_sync(self) -> int`: Method _get_users_count_sync.
  - `get_config(self, key) -> Optional[str]`: Method get_config.
  - `_get_config_sync(self, key) -> Optional[str]`: Method _get_config_sync.
  - `set_config(self, key, value) -> None`: Method set_config.
  - `_set_config_sync(self, key, value) -> None`: Method _set_config_sync.
  - `_update_cache(self, user_id, user_info) -> None`: Method _update_cache.

## Functions

None
