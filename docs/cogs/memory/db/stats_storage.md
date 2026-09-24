# File: `cogs/memory/db/stats_storage.py`

## Overview
StatsStorage: handles user statistics and log migration state persistence.

## Classes

### `StatsStorage`
Handles user_stats and log_migration_state table operations.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(db: DatabaseConnection) -> None`: Initialize with a DatabaseConnection instance.
  - `get_user_stats(user_id: str, guild_id: str) -> Optional[Dict[Tuple[str, Any]]]`: Retrieve cumulative stats for a user in a guild.
  - `_get_user_stats_sync(user_id: str, guild_id: str) -> Optional[Dict[Tuple[str, Any]]]`: No description provided.
  - `upsert_user_stats(user_id: str, guild_id: str, message_content: str, channel_id: str, timestamp: str) -> None`: Insert or update cumulative stats for a single message event.
  - `_upsert_user_stats_sync(user_id: str, guild_id: str, message_content: str, channel_id: str, timestamp: str) -> None`: No description provided.
  - `bulk_upsert_user_stats(records: List[Dict[Tuple[str, Any]]]) -> None`: Insert or update cumulative stats for a batch of message events.
  - `_bulk_upsert_user_stats_sync(records: List[Dict[Tuple[str, Any]]]) -> None`: No description provided.
  - `get_migration_state(guild_id: str) -> Optional[str]`: Get the last processed date for historical log migration.
  - `_get_migration_state_sync(guild_id: str) -> Optional[str]`: No description provided.
  - `set_migration_state(guild_id: str, date_str: str) -> None`: Record the last processed date for historical log migration.
  - `_set_migration_state_sync(guild_id: str, date_str: str) -> None`: No description provided.

## Functions

### `_safe_json_load(raw: Any) -> Dict[Tuple[str, int]]`
Safely parse a JSON string into a dict, defaulting to empty dict.

### `_extract_emojis(text: str) -> List[str]`
Extract Unicode and Discord custom emojis from text.

### `_segment_words(text: str) -> List[str]`
Segment text using jieba and filter stop-words / noise.

### `_trim_top_words(words_dict: Dict[Tuple[str, int]]) -> Dict[Tuple[str, int]]`
Keep only the top N words by frequency to prevent unbounded growth.

### `_compute_streak(current_streak: int, last_date_str: Optional[str], today_str: str) -> tuple[Tuple[int, str]]`
Compute the updated streak days based on the last active date.
