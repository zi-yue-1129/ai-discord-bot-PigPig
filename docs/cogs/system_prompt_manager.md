# File: `cogs/system_prompt_manager.py`

## Overview
頻道系統提示管理模組的主要 Cog

這個檔案作為系統提示管理模組的入口點，整合所有功能組件。

## Classes

### `SystemPromptManagerCog`
系統提示管理主要 Cog 類別

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `logger` (`Any`): Instance attribute managing logger.
  - `manager` (`Any`): Instance attribute managing manager.
  - `permission_validator` (`Any`): Instance attribute managing permission_validator.
  - `commands_cog` (`Any`): Instance attribute managing commands_cog.
  - `language_manager` (`Any`): Instance attribute managing language_manager.

- **Methods**:
  - `cog_load() -> Any`: Cog 載入時的初始化
  - `cog_unload() -> Any`: Cog 卸載時的清理
  - `get_system_prompt_manager() -> SystemPromptManager`: 取得系統提示管理器實例  這個方法供 gpt/sendmessage.py 調用，以整合系統提示功能。  Returns:     SystemPromptManager 實例
  - `get_permission_validator() -> PermissionValidator`: 取得權限驗證器實例  Returns:     PermissionValidator 實例
  - `get_effective_system_prompt(channel_id, guild_id, message) -> str`: 取得有效的系統提示（供外部模組調用的便利方法）  Args:     channel_id: 頻道 ID     guild_id: 伺服器 ID     message: Discord 訊息物件（可選）      Returns:     完整的系統提示字串
  - `validate_user_permission(user, action, target) -> bool`: 驗證用戶權限（供外部模組調用的便利方法）  Args:     user: Discord 用戶     action: 操作類型     target: 目標物件      Returns:     是否有權限
  - `on_guild_join(guild) -> Any`: 當機器人加入新伺服器時的處理
  - `on_guild_remove(guild) -> Any`: 當機器人離開伺服器時的處理
  - `system_prompt_status(ctx) -> Any`: View system prompt module status (bot owner only)
  - `clear_system_prompt_cache(ctx, guild_id) -> Any`: Clear system prompt cache (bot owner only)

## Functions

### `setup(bot) -> Any`
設定函式，用於載入 Cog

