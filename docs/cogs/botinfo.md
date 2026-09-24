# File: `cogs/botinfo.py`

## Overview
Core file handling responsibilities within the `cogs` subsystem.

## Classes

### `BotInfo`
Cog for displaying bot information and system statistics.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot) -> Any`: No description provided.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `_format_uptime(uptime, guild_id: str) -> Any`: Format uptime duration into a localized human-readable string.
  - `botinfo(interaction: discord.Interaction) -> Any`: Display comprehensive bot information and performance metrics.

## Functions

### `setup(bot) -> Any`
Set up the BotInfo cog.

