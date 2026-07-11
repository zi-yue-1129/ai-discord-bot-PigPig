# File: `cogs/stats_cog.py`

## Overview
The `StatsCog` is a specialized module designed for real-time user interaction tracking and historical log migration. It provides the foundation for "User Awareness" by maintaining a database of user activity across all servers the bot participates in.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `stats_cog.py`, providing vital integrations within the PigPig bot ecosystem.
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
  - `bot` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: commands.Bot) -> None`: Initialize StatsCog.
  - `cog_load() -> None`: Start background log migration task when cog loads.
  - `cog_unload() -> None`: Cancel background migration task on cog unload.
  - `on_message(message: Any) -> None`: Update user stats for every incoming message.
  - `_migrate_logs_background() -> None`: Ingest historical NDJSON log files into user_stats and stats.db.
  - `_migrate_guild_logs(guild_id: str, guild_dir: Path) -> None`: Migrate log files for a single guild.

## Functions

### `setup(bot: commands.Bot) -> None`
Register StatsCog with the bot.
