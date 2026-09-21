# File: `cogs/gif_tools.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `GifTools`
GIF 搜尋與管理工具。

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `tenor_api_key` (`Any`): Attribute holding tenor_api_key data.
  - `logger` (`Any`): Attribute holding logger data.
  - `lang_manager` (`Optional[LanguageManager]`): Attribute holding lang_manager data.

- **Methods**:
  - `__init__(bot) -> Any`: Executes __init__ logic.
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `search_gif(query: str, limit: int, guild_id: str) -> list`: 搜尋 GIF。
  - `search_gif_command(interaction: discord.Interaction, query: str) -> Any`: Discord 指令: 搜尋 GIF。
  - `get_gif_url(query: str, guild_id: str) -> str`: 取得隨機一個符合搜尋條件的 GIF URL。

## Functions

### `setup(bot) -> Any`
Performs setup operations.
