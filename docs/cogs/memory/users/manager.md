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
  - `storage` (`Any`): Instance attribute managing storage.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `get_user_info(user_id, use_cache) -> Optional[UserInfo]`: Retrieve user info via storage (storage handles its own caching).
  - `get_multiple_users(user_ids, use_cache) -> Dict[Tuple[str, UserInfo]]`: Retrieve multiple users concurrently (storage handles caching).
  - `update_user_data(user_id, user_data, discord_name, nickname) -> bool`: Extracts fields from user_data and delegates to storage.
  - `delete_user_data(user_id) -> bool`: Delegate deletion to storage.
  - `update_user_activity(user_id, discord_name, nickname) -> bool`: Delegate activity update to storage.
  - `search_users_by_display_name(name_pattern, limit) -> List[UserInfo]`: Search users by display name via storage.
  - `get_all_users(limit, offset) -> List[UserInfo]`: Return all users from storage; delegates to storage.get_all_users if available.
  - `get_users_count() -> int`: Return total user count from storage.
  - `get_user_statistics() -> Dict[Tuple[str, Any]]`: Return statistics from storage.
  - `migrate_from_mongodb(mongodb_collection) -> int`: Migrate users by delegating to update_user_data for each document.
  - `cleanup_inactive_users(days) -> int`: Delegate cleanup if storage provides method; otherwise no-op.

## Functions

### `extract_participant_ids(message, conversation_history) -> set`
Extract participant IDs from a message and recent conversation history.

Args:
    message: Discord message object
    conversation_history: list of recent messages or dicts representing messages

Returns:
    set: set of participant ID strings
