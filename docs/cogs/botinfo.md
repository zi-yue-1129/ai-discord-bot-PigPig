# File: `cogs/botinfo.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/botinfo.py`.

## Classes

### `BotInfo`
Cog for displaying bot information and system statistics.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `start_time` (`Any`): Instance attribute start_time
  - `lang_manager` (`Optional[LanguageManager]`): Instance attribute lang_manager

- **Methods**:
  - `cog_load(self) -> Any`: Initialize LanguageManager when the cog is loaded.
  - `_format_uptime(self, uptime, guild_id) -> Any`: Format uptime duration into a localized human-readable string.
  - `botinfo(self, interaction) -> Any`: Display comprehensive bot information and performance metrics.

## Functions

### `setup(bot) -> Any`
Set up the BotInfo cog.

