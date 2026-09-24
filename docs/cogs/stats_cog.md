# File: `cogs/stats_cog.py`

## Overview
StatsCog: real-time user statistics tracking and historical log migration.

## Classes

### `StatsCog`
Real-time user stats tracking and historical log migration.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: commands.Bot) -> None`: Initialize StatsCog.
  - `cog_load() -> None`: Start background log migration task when cog loads.
  - `cog_unload() -> None`: Cancel background migration task on cog unload.
  - `on_message(message) -> None`: Update user stats for every incoming message.
  - `_migrate_logs_background() -> None`: Ingest historical NDJSON log files into user_stats and stats.db.
  - `_migrate_guild_logs(guild_id: str, guild_dir: Path) -> None`: Migrate log files for a single guild.

## Functions

### `setup(bot: commands.Bot) -> None`
Register StatsCog with the bot.

