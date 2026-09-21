# File: `cogs/memory/users/manager.py`

## Overview
User manager depending on StorageInterface.

## Classes

### `SQLiteUserManager`
Lightweight user manager that delegates storage operations to StorageInterface.

Responsibilities:
- delegate persistence to provided storage
- coordinate user data operations

- **Attributes**:
  - `storage` (`Any`): Attribute holding storage data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(storage: StorageInterface) -> Any`: Initialize with a StorageInterface implementation.
  - `get_user_info(user_id: str, use_cache: bool) -> Optional[UserInfo]`: Retrieve user info via storage (storage handles its own caching).
  - `get_multiple_users(user_ids: List[str], use_cache: bool) -> Dict[Tuple[str, UserInfo]]`: Retrieve multiple users concurrently (storage handles caching).
  - `update_user_data(user_id: str, user_data: Any, discord_name: Optional[str], nickname: Optional[str]) -> bool`: Extracts fields from user_data and delegates to storage.
  - `delete_user_data(user_id: str) -> bool`: Delegate deletion to storage.
  - `update_user_activity(user_id: str, discord_name: str, nickname: Optional[str]) -> bool`: Delegate activity update to storage.
  - `search_users_by_display_name(name_pattern: str, limit: int) -> List[UserInfo]`: Search users by display name via storage.
  - `get_all_users(limit: int, offset: int) -> List[UserInfo]`: Return all users from storage; delegates to storage.get_all_users if available.
  - `get_users_count() -> int`: Return total user count from storage.
  - `get_user_statistics() -> Dict[Tuple[str, Any]]`: Return statistics from storage.
  - `migrate_from_mongodb(mongodb_collection) -> int`: Migrate users by delegating to update_user_data for each document.
  - `cleanup_inactive_users(days: int) -> int`: Delegate cleanup if storage provides method; otherwise no-op.

## Functions

### `extract_participant_ids(message, conversation_history: List[Any]) -> set`
Extract participant IDs from a message and recent conversation history.

Args:
    message: Discord message object
    conversation_history: list of recent messages or dicts representing messages

Returns:
    set: set of participant ID strings
