# File: `cogs/gif_tools.py`

## Overview
The GIF Tools cog provides comprehensive GIF search and processing capabilities for Discord users. It enables users to search for GIFs from various sources, process and edit GIFs, and share animated content with their Discord communities through a simple and intuitive interface.

## Classes

### `GifTools`
GIF 搜尋與管理工具。

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `tenor_api_key` (`Any`): Instance attribute managing tenor_api_key.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `search_gif(query, limit, guild_id) -> list`: 搜尋 GIF。  Args:     query: 搜尋關鍵字。     limit: 返回結果數量，預設為 1。           建議保持較小的數值以提高相關性。     guild_id: 伺服器 ID，用於翻譯，預設為 "0"。  Returns:     list: GIF URL 列表。如果搜尋失敗則返回空列表。
  - `search_gif_command(interaction, query) -> Any`: Discord 指令: 搜尋 GIF。
  - `get_gif_url(query, guild_id) -> str`: 取得隨機一個符合搜尋條件的 GIF URL。  Args:     query: 搜尋關鍵字。           例如："happy cat", "sad dog" 等描述性短語。     guild_id: 伺服器 ID，用於翻譯，預設為 "0"。  Returns:     str: GIF URL，如果找不到則返回空字串。

## Functions

### `setup(bot) -> Any`
Performs setup operations.

