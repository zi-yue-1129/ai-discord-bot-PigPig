# File: `cogs/gif_tools.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `gif_tools` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `GifTools`
GIF 搜尋與管理工具。

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `tenor_api_key` (`Any`): Instance attribute for tenor_api_key.
  - `logger` (`Any`): Instance attribute for logger.
  - `lang_manager` (`Optional[...]`): Instance attribute for lang_manager.

- **Methods**:
  - `__init__(bot) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `ValueError`.
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `search_gif(query, limit, guild_id) -> list`: 搜尋 GIF。
  - `search_gif_command(interaction, query) -> Any`: Discord 指令: 搜尋 GIF。
  - `get_gif_url(query, guild_id) -> str`: 取得隨機一個符合搜尋條件的 GIF URL。

## Functions

### `setup(bot) -> Any`
Provides `setup` functionality. Internally, it interacts with methods like `warning` and `add_cog`.
