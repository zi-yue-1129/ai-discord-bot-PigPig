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
  - `db` (`Any`): Instance attribute managing db.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `get_user_stats(user_id, guild_id) -> Optional[Dict[Tuple[str, Any]]]`: Retrieve cumulative stats for a user in a guild.
  - `upsert_user_stats(user_id, guild_id, message_content, channel_id, timestamp) -> None`: Insert or update cumulative stats for a single message event.
  - `bulk_upsert_user_stats(records) -> None`: Insert or update cumulative stats for a batch of message events.
  - `get_migration_state(guild_id) -> Optional[str]`: Get the last processed date for historical log migration.
  - `set_migration_state(guild_id, date_str) -> None`: Record the last processed date for historical log migration.
