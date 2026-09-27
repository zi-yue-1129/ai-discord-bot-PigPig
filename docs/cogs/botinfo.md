# File: `cogs/botinfo.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `botinfo` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `BotInfo`
Cog for displaying bot information and system statistics.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `start_time` (`Any`): Instance attribute for start_time.
  - `lang_manager` (`Optional[...]`): Instance attribute for lang_manager.

- **Methods**:
  - `__init__(bot) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `utcnow`.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `_format_uptime(uptime, guild_id) -> Any`: Format uptime duration into a localized human-readable string.
  - `botinfo(interaction) -> Any`: Display comprehensive bot information and performance metrics.

## Functions

### `setup(bot) -> Any`
Set up the BotInfo cog.
