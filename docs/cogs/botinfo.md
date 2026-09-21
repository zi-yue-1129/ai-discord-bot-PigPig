# File: `cogs/botinfo.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `BotInfo`
Cog for displaying bot information and system statistics.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `start_time` (`Any`): Attribute holding start_time data.
  - `lang_manager` (`Optional[LanguageManager]`): Attribute holding lang_manager data.

- **Methods**:
  - `__init__(bot) -> Any`: Executes __init__ logic.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `_format_uptime(uptime, guild_id: str) -> Any`: Format uptime duration into a localized human-readable string.
  - `botinfo(interaction: discord.Interaction) -> Any`: Display comprehensive bot information and performance metrics.

## Functions

### `setup(bot) -> Any`
Set up the BotInfo cog.
