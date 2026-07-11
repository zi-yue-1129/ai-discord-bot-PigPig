# File: `cogs/help.py`

## Overview
The Help cog provides a comprehensive command help system with multi-language support. It dynamically generates help content by inspecting all loaded cogs and their available commands.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `help.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `HelpCog`
Class managing HelpCog state and behavior.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any) -> Any`: Performs internal processing logic.
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `_translate(guild_id: str) -> str`: Helper to translate with a safe fallback when keys are missing.
  - `_chunk_field_values(lines: List[str], limit: int) -> List[str]`: Split command lines into chunks that respect Discord's 1024-char field limit.
  - `_create_embed_page(title: str, description: Optional[str]) -> discord.Embed`: Create a new embed page for the help command.
  - `_build_help_embeds(guild_id: str, title: str, description: str) -> List[discord.Embed]`: Construct one or more embeds while respecting Discord limits.
  - `help_command(interaction: discord.Interaction) -> Any`: Performs internal processing logic.

## Functions

### `setup(bot: Any) -> Any`
Performs internal processing logic.
