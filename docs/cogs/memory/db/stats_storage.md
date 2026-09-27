# File: `cogs/memory/db/stats_storage.py`

## Overview
StatsStorage: handles user statistics and log migration state persistence.

This module provides CRUD operations for the user_stats and
log_migration_state tables, supporting real-time message tracking and
historical log migration.

## Classes

### `StatsStorage`
Handles user_stats and log_migration_state table operations.

Attributes:
    db: The shared DatabaseConnection instance.

- **Attributes**:
  - `db` (`Any`): Instance attribute for db.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(db) -> None`: Initialize with a DatabaseConnection instance.
  - `get_user_stats(user_id, guild_id) -> Optional[...]`: Retrieve cumulative stats for a user in a guild.
  - `_get_user_stats_sync(user_id, guild_id) -> Optional[...]`: Handles the `_get_user_stats_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
  - `upsert_user_stats(user_id, guild_id, message_content, channel_id, timestamp) -> None`: Insert or update cumulative stats for a single message event.
  - `_upsert_user_stats_sync(user_id, guild_id, message_content, channel_id, timestamp) -> None`: Handles the `_upsert_user_stats_sync` functionality. Internally, it interacts with methods like `strftime` and `_extract_emojis`.
  - `bulk_upsert_user_stats(records) -> None`: Insert or update cumulative stats for a batch of message events.
  - `_bulk_upsert_user_stats_sync(records) -> None`: Handles the `_bulk_upsert_user_stats_sync` functionality. Internally, it interacts with methods like `get_connection` and `commit`.
  - `get_migration_state(guild_id) -> Optional[...]`: Get the last processed date for historical log migration.
  - `_get_migration_state_sync(guild_id) -> Optional[...]`: Handles the `_get_migration_state_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.
  - `set_migration_state(guild_id, date_str) -> None`: Record the last processed date for historical log migration.
  - `_set_migration_state_sync(guild_id, date_str) -> None`: Handles the `_set_migration_state_sync` functionality. Internally, it interacts with methods like `get_connection` and `execute`.

## Functions

### `_safe_json_load(raw) -> Dict[...]`
Safely parse a JSON string into a dict, defaulting to empty dict.

### `_extract_emojis(text) -> List[...]`
Extract Unicode and Discord custom emojis from text.

### `_segment_words(text) -> List[...]`
Segment text using jieba and filter stop-words / noise.

### `_trim_top_words(words_dict) -> Dict[...]`
Keep only the top N words by frequency to prevent unbounded growth.

### `_compute_streak(current_streak, last_date_str, today_str) -> tuple[...]`
Compute the updated streak days based on the last active date.
