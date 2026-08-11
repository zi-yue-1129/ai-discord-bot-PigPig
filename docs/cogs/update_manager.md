# File: `cogs/update_manager.py`

## Overview
Discord 更新管理 Cog

提供 Discord 命令介面來管理自動更新系統。

## Classes

### `UpdateManagerCog`
Discord 更新管理介面

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `cog_load() -> Any`: Cog 載入時初始化語言管理器
  - `check_update(interaction) -> Any`: 檢查更新命令
  - `update_now(interaction, force) -> Any`: 立即更新命令  Args:     force: 是否強制更新（即使沒有新版本）
  - `update_status(interaction) -> Any`: 更新狀態查詢
  - `configure_update(interaction) -> Any`: 更新配置命令

### `UpdateActionView`
更新操作視圖

- **Attributes**:
  - `update_manager` (`Any`): Instance attribute managing update_manager.
  - `guild_id` (`Any`): Instance attribute managing guild_id.
  - `get_translation` (`Any`): Instance attribute managing get_translation.

- **Methods**:
  - `update_now(interaction, button) -> Any`: 立即更新按鈕
  - `remind_later(interaction, button) -> Any`: 稍後提醒按鈕

### `UpdateConfirmView`
更新確認視圖

- **Attributes**:
  - `update_manager` (`Any`): Instance attribute managing update_manager.
  - `version_info` (`Any`): Instance attribute managing version_info.
  - `guild_id` (`Any`): Instance attribute managing guild_id.
  - `get_translation` (`Any`): Instance attribute managing get_translation.
  - `force` (`Any`): Instance attribute managing force.

- **Methods**:
  - `confirm_update(interaction, button) -> Any`: 確認更新按鈕
  - `cancel_update(interaction, button) -> Any`: 取消更新按鈕

### `UpdateConfigView`
更新配置視圖

- **Attributes**:
  - `update_manager` (`Any`): Instance attribute managing update_manager.
  - `guild_id` (`Any`): Instance attribute managing guild_id.
  - `get_translation` (`Any`): Instance attribute managing get_translation.

- **Methods**:
  - `toggle_auto_update(interaction, button) -> Any`: 切換自動更新開關
  - `set_check_interval(interaction, button) -> Any`: 設定檢查間隔

## Functions

### `setup(bot) -> Any`
設定 Cog

