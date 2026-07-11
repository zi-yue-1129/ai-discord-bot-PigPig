# File: `cogs/update_manager.py`

## Overview
The Update Manager cog provides comprehensive automated update and deployment management capabilities for the Discord bot. It handles system updates, dependency management, configuration synchronization, backup operations, and rollback functionality. This cog ensures the bot stays current with the latest features while maintaining system stability through careful update procedures and reliable rollback mechanisms.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `update_manager.py`, providing vital integrations within the PigPig bot ecosystem.
Discord 更新管理 Cog

提供 Discord 命令介面來管理自動更新系統。

## Classes

### `UpdateManagerCog`
Discord 更新管理介面

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any) -> Any`: 初始化更新管理 Cog
  - `cog_load() -> Any`: Cog 載入時初始化語言管理器
  - `_get_translation(guild_id: str) -> str`: 取得翻譯文字的安全方法
  - `check_update(interaction: discord.Interaction) -> Any`: 檢查更新命令
  - `update_now(interaction: discord.Interaction, force: bool) -> Any`: 立即更新命令
  - `update_status(interaction: discord.Interaction) -> Any`: 更新狀態查詢
  - `configure_update(interaction: discord.Interaction) -> Any`: 更新配置命令
  - `_create_status_embed(status: dict, guild_id: str) -> discord.Embed`: 創建狀態嵌入

### `UpdateActionView`
更新操作視圖

- **Attributes**:
  - `update_manager` (`Any`): Internal instance state.
  - `guild_id` (`Any`): Internal instance state.
  - `get_translation` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(update_manager: Any, guild_id: str, get_translation_func: Any) -> Any`: Performs internal processing logic.
  - `update_now(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 立即更新按鈕
  - `remind_later(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 稍後提醒按鈕

### `UpdateConfirmView`
更新確認視圖

- **Attributes**:
  - `update_manager` (`Any`): Internal instance state.
  - `version_info` (`Any`): Internal instance state.
  - `guild_id` (`Any`): Internal instance state.
  - `get_translation` (`Any`): Internal instance state.
  - `force` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(update_manager: Any, version_info: Any, guild_id: str, get_translation_func: Any, force: Any) -> Any`: Performs internal processing logic.
  - `confirm_update(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 確認更新按鈕
  - `cancel_update(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 取消更新按鈕
  - `_execute_update(interaction: Any) -> Any`: 執行更新

### `UpdateConfigView`
更新配置視圖

- **Attributes**:
  - `update_manager` (`Any`): Internal instance state.
  - `guild_id` (`Any`): Internal instance state.
  - `get_translation` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(update_manager: Any, guild_id: str, get_translation_func: Any) -> Any`: Performs internal processing logic.
  - `toggle_auto_update(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 切換自動更新開關
  - `set_check_interval(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 設定檢查間隔

## Functions

### `setup(bot: Any) -> Any`
設定 Cog
