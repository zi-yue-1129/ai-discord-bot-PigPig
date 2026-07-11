# File: `cogs/botinfo.py`

## Overview
The BotInfo cog provides comprehensive bot information display and system monitoring capabilities. It offers both basic statistics and performance metrics through Discord embeds.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `botinfo.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `BotInfo`
Cog for displaying bot information and system statistics.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `start_time` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any) -> Any`: Performs internal processing logic.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `_format_uptime(uptime: Any, guild_id: str) -> Any`: Format uptime duration into a localized human-readable string.
  - `botinfo(interaction: discord.Interaction) -> Any`: Display comprehensive bot information and performance metrics.

## Functions

### `setup(bot: Any) -> Any`
Set up the BotInfo cog.
