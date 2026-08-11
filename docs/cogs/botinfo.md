# File: `cogs/botinfo.py`

## Overview
The BotInfo cog provides comprehensive bot information display and system monitoring capabilities. It offers both basic statistics and performance metrics through Discord embeds.

## Classes

### `BotInfo`
Cog for displaying bot information and system statistics.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `start_time` (`Any`): Instance attribute managing start_time.

- **Methods**:
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `botinfo(interaction) -> Any`: Display comprehensive bot information and performance metrics.

## Functions

### `setup(bot) -> Any`
Set up the BotInfo cog.

