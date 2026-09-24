# File: `cogs/update_manager.py`

## Overview
Discord 更新管理 Cog

## Classes

### `UpdateManagerCog`
Discord 更新管理介面

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot) -> Any`: 初始化更新管理 Cog
  - `cog_load() -> Any`: Cog 載入時初始化語言管理器
  - `_get_translation(guild_id: str, *keys, **kwargs) -> str`: 取得翻譯文字的安全方法
  - `check_update(interaction: discord.Interaction) -> Any`: 檢查更新命令
  - `update_now(interaction: discord.Interaction, force: bool) -> Any`: 立即更新命令
  - `update_status(interaction: discord.Interaction) -> Any`: 更新狀態查詢
  - `configure_update(interaction: discord.Interaction) -> Any`: 更新配置命令
  - `_create_status_embed(status: dict, guild_id: str) -> discord.Embed`: 創建狀態嵌入

### `UpdateActionView`
更新操作視圖

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(update_manager, guild_id: str, get_translation_func) -> Any`: No description provided.
  - `update_now(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 立即更新按鈕
  - `remind_later(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 稍後提醒按鈕

### `UpdateConfirmView`
更新確認視圖

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(update_manager, version_info, guild_id: str, get_translation_func, force) -> Any`: No description provided.
  - `confirm_update(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 確認更新按鈕
  - `cancel_update(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 取消更新按鈕
  - `_execute_update(interaction) -> Any`: 執行更新

### `UpdateConfigView`
更新配置視圖

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(update_manager, guild_id: str, get_translation_func) -> Any`: No description provided.
  - `toggle_auto_update(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 切換自動更新開關
  - `set_check_interval(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 設定檢查間隔

## Functions

### `setup(bot) -> Any`
設定 Cog

