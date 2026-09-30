# File: `cogs/update_manager.py`

## Overview
Discord 更新管理 Cog

提供 Discord 命令介面來管理自動更新系統。

## Classes

### `UpdateManagerCog`
Discord 更新管理介面

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `logger` (`Any`): Instance attribute logger
  - `lang_manager` (`Optional[LanguageManager]`): Instance attribute lang_manager
  - `update_manager` (`Any`): Instance attribute update_manager
  - `permission_checker` (`Any`): Instance attribute permission_checker

- **Methods**:
  - `cog_load(self) -> Any`: Cog 載入時初始化語言管理器
  - `_get_translation(self, guild_id, *keys, **kwargs) -> str`: 取得翻譯文字的安全方法
  - `check_update(self, interaction) -> Any`: 檢查更新命令
  - `update_now(self, interaction, force) -> Any`: 立即更新命令  Args:     force: 是否強制更新（即使沒有新版本）
  - `update_status(self, interaction) -> Any`: 更新狀態查詢
  - `configure_update(self, interaction) -> Any`: 更新配置命令
  - `_create_status_embed(self, status, guild_id) -> discord.Embed`: 創建狀態嵌入

### `UpdateActionView`
更新操作視圖

- **Attributes**:
  - `update_manager` (`Any`): Instance attribute update_manager
  - `guild_id` (`Any`): Instance attribute guild_id
  - `get_translation` (`Any`): Instance attribute get_translation

- **Methods**:
  - `update_now(self, interaction, button) -> Any`: 立即更新按鈕
  - `remind_later(self, interaction, button) -> Any`: 稍後提醒按鈕

### `UpdateConfirmView`
更新確認視圖

- **Attributes**:
  - `update_manager` (`Any`): Instance attribute update_manager
  - `version_info` (`Any`): Instance attribute version_info
  - `guild_id` (`Any`): Instance attribute guild_id
  - `get_translation` (`Any`): Instance attribute get_translation
  - `force` (`Any`): Instance attribute force

- **Methods**:
  - `confirm_update(self, interaction, button) -> Any`: 確認更新按鈕
  - `cancel_update(self, interaction, button) -> Any`: 取消更新按鈕
  - `_execute_update(self, interaction) -> Any`: 執行更新

### `UpdateConfigView`
更新配置視圖

- **Attributes**:
  - `update_manager` (`Any`): Instance attribute update_manager
  - `guild_id` (`Any`): Instance attribute guild_id
  - `get_translation` (`Any`): Instance attribute get_translation

- **Methods**:
  - `toggle_auto_update(self, interaction, button) -> Any`: 切換自動更新開關
  - `set_check_interval(self, interaction, button) -> Any`: 設定檢查間隔

## Functions

### `setup(bot) -> Any`
設定 Cog

