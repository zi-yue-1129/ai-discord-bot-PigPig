# File: `cogs/help.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `HelpCog`
Core class implementation.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `lang_manager` (`Optional[LanguageManager]`): Attribute holding lang_manager data.

- **Methods**:
  - `__init__(bot) -> Any`: Executes __init__ logic.
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `_translate(guild_id: str, *keys, default: str) -> str`: Helper to translate with a safe fallback when keys are missing.
  - `_chunk_field_values(lines: List[str], limit: int) -> List[str]`: Split command lines into chunks that respect Discord's 1024-char field limit.
  - `_create_embed_page(title: str, description: Optional[str]) -> discord.Embed`: Create a new embed page for the help command.
  - `_build_help_embeds(guild_id: str, title: str, description: str) -> List[discord.Embed]`: Construct one or more embeds while respecting Discord limits.
  - `help_command(interaction: discord.Interaction) -> Any`: Executes help_command logic.

## Functions

### `setup(bot) -> Any`
Performs setup operations.
