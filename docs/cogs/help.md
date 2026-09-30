# File: `cogs/help.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/help.py`.

## Classes

### `HelpCog`
Class representing HelpCog.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `lang_manager` (`Optional[LanguageManager]`): Instance attribute lang_manager

- **Methods**:
  - `cog_load(self) -> Any`: 當 Cog 載入時初始化語言管理器
  - `_translate(self, guild_id, *keys) -> str`: Helper to translate with a safe fallback when keys are missing.
  - `_chunk_field_values(self, lines, limit) -> List[str]`: Split command lines into chunks that respect Discord's 1024-char field limit.
  - `_create_embed_page(self, title, description) -> discord.Embed`: Create a new embed page for the help command.
  - `_build_help_embeds(self, guild_id, title, description) -> List[discord.Embed]`: Construct one or more embeds while respecting Discord limits.
  - `help_command(self, interaction) -> Any`: Method help_command.

## Functions

### `setup(bot) -> Any`
Function setup.

