# File: `cogs/gif_tools.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/gif_tools.py`.

## Classes

### `GifTools`
GIF 搜尋與管理工具。

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `tenor_api_key` (`Any`): Instance attribute tenor_api_key
  - `logger` (`Any`): Instance attribute logger
  - `lang_manager` (`Optional[LanguageManager]`): Instance attribute lang_manager

- **Methods**:
  - `cog_load(self) -> Any`: 當 Cog 載入時初始化語言管理器
  - `search_gif(self, query, limit, guild_id) -> list`: 搜尋 GIF。  Args:     query: 搜尋關鍵字。     limit: 返回結果數量，預設為 1。           建議保持較小的數值以提高相關性。     guild_id: 伺服器 ID，用於翻譯，預設為 "0"。  Returns:     list: GIF URL 列表。如果搜尋失敗則返回空列表。
  - `search_gif_command(self, interaction, query) -> Any`: Discord 指令: 搜尋 GIF。
  - `get_gif_url(self, query, guild_id) -> str`: 取得隨機一個符合搜尋條件的 GIF URL。  Args:     query: 搜尋關鍵字。           例如："happy cat", "sad dog" 等描述性短語。     guild_id: 伺服器 ID，用於翻譯，預設為 "0"。  Returns:     str: GIF URL，如果找不到則返回空字串。

## Functions

### `setup(bot) -> Any`
Function setup.

