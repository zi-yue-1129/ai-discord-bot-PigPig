# File: `cogs/memory/db/procedural_storage.py`

## Overview
ProceduralStorage: handles users table and configuration storage.

## Classes

### `ProceduralStorage`
Handles users table and config storage.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(db: DatabaseConnection) -> None`: No description provided.
  - `get_user_info(discord_id: str) -> Optional[UserInfo]`: No description provided.
  - `_get_user_info_sync(discord_id: str) -> Optional[UserInfo]`: No description provided.
  - `get_users_info(discord_ids: List[str]) -> Dict[Tuple[str, UserInfo]]`: Fetch multiple users efficiently using a single SQL query.
  - `update_user_data(discord_id: str, discord_name: str, procedural_memory: Optional[str], user_background: Optional[str], display_names: Optional[List[str]], nickname: Optional[str]) -> bool`: No description provided.
  - `_update_user_data_sync(discord_id: str, discord_name: str, procedural_memory: Optional[str], user_background: Optional[str], display_names: Optional[List[str]], nickname: Optional[str]) -> bool`: No description provided.
  - `delete_user_data(discord_id: str) -> bool`: No description provided.
  - `_delete_user_data_sync(discord_id: str) -> bool`: No description provided.
  - `update_user_activity(discord_id: str, discord_name: str, nickname: Optional[str]) -> bool`: No description provided.
  - `_update_user_activity_sync(discord_id: str, discord_name: str, nickname: Optional[str]) -> bool`: No description provided.
  - `get_all_users(limit: int, offset: int) -> List[UserInfo]`: Return all users ordered by creation date (newest first).
  - `_get_all_users_sync(limit: int, offset: int) -> List[UserInfo]`: No description provided.
  - `get_users_count() -> int`: Return total number of users in the database.
  - `_get_users_count_sync() -> int`: No description provided.
  - `get_config(key: str) -> Optional[str]`: No description provided.
  - `_get_config_sync(key: str) -> Optional[str]`: No description provided.
  - `set_config(key: str, value: str) -> None`: No description provided.
  - `_set_config_sync(key: str, value: str) -> None`: No description provided.
  - `_update_cache(user_id: str, user_info: UserInfo) -> None`: No description provided.

## Functions

No module-level functions defined in this file.
