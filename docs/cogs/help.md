# File: `cogs/help.py`

## Overview
Core file handling responsibilities within the `cogs` subsystem.

## Classes

### `HelpCog`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot) -> Any`: No description provided.
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `_translate(guild_id: str, *keys: str, default: str) -> str`: Helper to translate with a safe fallback when keys are missing.
  - `_chunk_field_values(lines: List[str], limit: int) -> List[str]`: Split command lines into chunks that respect Discord's 1024-char field limit.
  - `_create_embed_page(title: str, description: Optional[str]) -> discord.Embed`: Create a new embed page for the help command.
  - `_build_help_embeds(guild_id: str, title: str, description: str) -> List[discord.Embed]`: Construct one or more embeds while respecting Discord limits.
  - `help_command(interaction: discord.Interaction) -> Any`: No description provided.

## Functions

### `setup(bot) -> Any`
No description provided.

