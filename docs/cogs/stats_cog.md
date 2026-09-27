# File: `cogs/stats_cog.py`

## Overview
StatsCog: real-time user statistics tracking and historical log migration.

Listens for on_message events to update per-user stats in the user_stats
table, and runs a low-priority background task on cog load to ingest
historical NDJSON log files.

## Classes

### `StatsCog`
Real-time user stats tracking and historical log migration.

Attributes:
    bot: The Discord bot instance.
    stats_storage: StatsStorage instance for DB operations.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `stats_storage` (`Optional[...]`): Instance attribute for stats_storage.
  - `_migration_task` (`Optional[...]`): Instance attribute for _migration_task.

- **Methods**:
  - `__init__(bot) -> None`: Initialize StatsCog.
  - `cog_load() -> None`: Start background log migration task when cog loads.
  - `cog_unload() -> None`: Cancel background migration task on cog unload.
  - `on_message(message) -> None`: Update user stats for every incoming message.
  - `_migrate_logs_background() -> None`: Ingest historical NDJSON log files into user_stats and stats.db.
  - `_migrate_guild_logs(guild_id, guild_dir) -> None`: Migrate log files for a single guild.

## Functions

### `setup(bot) -> None`
Register StatsCog with the bot.
