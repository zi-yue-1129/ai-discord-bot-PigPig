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
  - `bot` (`Any`): Instance attribute managing bot.

- **Methods**:
  - `cog_load() -> None`: Start background log migration task when cog loads.
  - `cog_unload() -> None`: Cancel background migration task on cog unload.
  - `on_message(message) -> None`: Update user stats for every incoming message.  Args:     message: The Discord message object.

## Functions

### `setup(bot) -> None`
Register StatsCog with the bot.

