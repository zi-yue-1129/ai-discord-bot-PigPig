# File: `cogs/gif_tools.py`

## Overview
Core file handling responsibilities within the `cogs` subsystem.

## Classes

### `GifTools`
GIF 搜尋與管理工具。

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot) -> Any`: No description provided.
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `search_gif(query: str, limit: int, guild_id: str) -> list`: 搜尋 GIF。
  - `search_gif_command(interaction: discord.Interaction, query: str) -> Any`: Discord 指令: 搜尋 GIF。
  - `get_gif_url(query: str, guild_id: str) -> str`: 取得隨機一個符合搜尋條件的 GIF URL。

## Functions

### `setup(bot) -> Any`
No description provided.

