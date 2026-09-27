# File: `cogs/update_manager.py`

## Overview
Discord 更新管理 Cog

提供 Discord 命令介面來管理自動更新系統。

## Classes

### `UpdateManagerCog`
Discord 更新管理介面

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `logger` (`Any`): Instance attribute for logger.
  - `lang_manager` (`Optional[...]`): Instance attribute for lang_manager.

- **Methods**:
  - `__init__(bot) -> Any`: 初始化更新管理 Cog
  - `cog_load() -> Any`: Cog 載入時初始化語言管理器
  - `_get_translation(guild_id, *keys, **kwargs) -> str`: 取得翻譯文字的安全方法
  - `check_update(interaction) -> Any`: 檢查更新命令
  - `update_now(interaction, force) -> Any`: 立即更新命令
  - `update_status(interaction) -> Any`: 更新狀態查詢
  - `configure_update(interaction) -> Any`: 更新配置命令
  - `_create_status_embed(status, guild_id) -> discord.Embed`: 創建狀態嵌入

### `UpdateActionView`
更新操作視圖

- **Attributes**:
  - `update_manager` (`Any`): Instance attribute for update_manager.
  - `guild_id` (`Any`): Instance attribute for guild_id.
  - `get_translation` (`Any`): Instance attribute for get_translation.

- **Methods**:
  - `__init__(update_manager, guild_id, get_translation_func) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__`.
  - `update_now(interaction, button) -> Any`: 立即更新按鈕
  - `remind_later(interaction, button) -> Any`: 稍後提醒按鈕

### `UpdateConfirmView`
更新確認視圖

- **Attributes**:
  - `update_manager` (`Any`): Instance attribute for update_manager.
  - `version_info` (`Any`): Instance attribute for version_info.
  - `guild_id` (`Any`): Instance attribute for guild_id.
  - `get_translation` (`Any`): Instance attribute for get_translation.
  - `force` (`Any`): Instance attribute for force.

- **Methods**:
  - `__init__(update_manager, version_info, guild_id, get_translation_func, force) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__`.
  - `confirm_update(interaction, button) -> Any`: 確認更新按鈕
  - `cancel_update(interaction, button) -> Any`: 取消更新按鈕
  - `_execute_update(interaction) -> Any`: 執行更新

### `UpdateConfigView`
更新配置視圖

- **Attributes**:
  - `update_manager` (`Any`): Instance attribute for update_manager.
  - `guild_id` (`Any`): Instance attribute for guild_id.
  - `get_translation` (`Any`): Instance attribute for get_translation.

- **Methods**:
  - `__init__(update_manager, guild_id, get_translation_func) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__`.
  - `toggle_auto_update(interaction, button) -> Any`: 切換自動更新開關
  - `set_check_interval(interaction, button) -> Any`: 設定檢查間隔

## Functions

### `setup(bot) -> Any`
設定 Cog
