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
  - `db` (`Any`): Instance attribute for db.
  - `_user_cache` (`Dict[...]`): Instance attribute for _user_cache.
  - `_cache_size_limit` (`Any`): Instance attribute for _cache_size_limit.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(db) -> None`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `get_user_info(discord_id) -> Optional[...]`: Handles the `get_user_info` functionality. Internally, it interacts with methods like `to_thread` and `report_error`.
  - `_get_user_info_sync(discord_id) -> Optional[...]`: Handles the `_get_user_info_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
  - `get_users_info(discord_ids) -> Dict[...]`: Fetch multiple users efficiently using a single SQL query.
  - `update_user_data(discord_id, discord_name, procedural_memory, user_background, display_names, nickname) -> bool`: Handles the `update_user_data` functionality. Internally, it interacts with methods like `to_thread` and `report_error`.
  - `_update_user_data_sync(discord_id, discord_name, procedural_memory, user_background, display_names, nickname) -> bool`: Handles the `_update_user_data_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
  - `delete_user_data(discord_id) -> bool`: Handles the `delete_user_data` functionality. Internally, it interacts with methods like `to_thread` and `report_error`.
  - `_delete_user_data_sync(discord_id) -> bool`: Handles the `_delete_user_data_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
  - `update_user_activity(discord_id, discord_name, nickname) -> bool`: Handles the `update_user_activity` functionality. Internally, it interacts with methods like `to_thread` and `report_error`.
  - `_update_user_activity_sync(discord_id, discord_name, nickname) -> bool`: Handles the `_update_user_activity_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
  - `get_all_users(limit, offset) -> List[...]`: Return all users ordered by creation date (newest first).
  - `_get_all_users_sync(limit, offset) -> List[...]`: Handles the `_get_all_users_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
  - `get_users_count() -> int`: Return total number of users in the database.
  - `_get_users_count_sync() -> int`: Handles the `_get_users_count_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
  - `get_config(key) -> Optional[...]`: Handles the `get_config` functionality. Internally, it interacts with methods like `to_thread` and `report_error`.
  - `_get_config_sync(key) -> Optional[...]`: Handles the `_get_config_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
  - `set_config(key, value) -> None`: Handles the `set_config` functionality. Internally, it interacts with methods like `to_thread` and `report_error`.
  - `_set_config_sync(key, value) -> None`: Handles the `_set_config_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
  - `_update_cache(user_id, user_info) -> None`: Handles the `_update_cache` functionality. Internally, it interacts with methods like `next` and `exception`.
