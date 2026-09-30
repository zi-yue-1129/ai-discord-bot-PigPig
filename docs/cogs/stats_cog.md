# File: `cogs/stats_cog.py`

## Overview
StatsCog: real-time user statistics tracking and historical log migration.

Listens for on_message events to update per-user stats in the user_stats
table, and runs a low-priority background task on cog load to ingest
historical NDJSON log files.

## Classes

### `StatsCog`
Real-time user stats tracking and historical log migration.  Attributes:     bot: The Discord bot instance.     stats_storage: StatsStorage instance for DB operations.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `stats_storage` (`Optional[StatsStorage]`): Instance attribute stats_storage
  - `_migration_task` (`Optional[asyncio.Task]`): Instance attribute _migration_task

- **Methods**:
  - `cog_load(self) -> None`: Start background log migration task when cog loads.
  - `cog_unload(self) -> None`: Cancel background migration task on cog unload.
  - `on_message(self, message) -> None`: Update user stats for every incoming message.  Args:     message: The Discord message object.
  - `_migrate_logs_background(self) -> None`: Ingest historical NDJSON log files into user_stats and stats.db.  Processes logs/{guild_id}/{YYYYMMDD}/info.jsonl files that have not been processed yet (tracked via log_migration_state table).
  - `_migrate_guild_logs(self, guild_id, guild_dir) -> None`: Migrate log files for a single guild.  Args:     guild_id: The guild's Discord snowflake ID.     guild_dir: Path to the guild's log directory.

## Functions

### `setup(bot) -> None`
Register StatsCog with the bot.

