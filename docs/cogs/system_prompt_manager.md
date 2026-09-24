# File: `cogs/system_prompt_manager.py`

## Overview
頻道系統提示管理模組的主要 Cog

## Classes

### `SystemPromptManagerCog`
系統提示管理主要 Cog 類別

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: commands.Bot) -> Any`: 初始化系統提示管理 Cog
  - `_get_language_manager() -> Any`: 安全地取得語言管理器實例
  - `_translate(guild_id: str, *keys) -> Any`: 安全的翻譯方法，使用 getattr 避免類型檢查問題
  - `cog_load() -> Any`: Cog 載入時的初始化
  - `cog_unload() -> Any`: Cog 卸載時的清理
  - `get_system_prompt_manager() -> SystemPromptManager`: 取得系統提示管理器實例
  - `get_permission_validator() -> PermissionValidator`: 取得權限驗證器實例
  - `get_effective_system_prompt(channel_id: str, guild_id: str, message: Optional[discord.Message]) -> str`: 取得有效的系統提示（供外部模組調用的便利方法）
  - `validate_user_permission(user: discord.Member, action: str, target: any) -> bool`: 驗證用戶權限（供外部模組調用的便利方法）
  - `on_guild_join(guild: discord.Guild) -> Any`: 當機器人加入新伺服器時的處理
  - `on_guild_remove(guild: discord.Guild) -> Any`: 當機器人離開伺服器時的處理
  - `system_prompt_status(ctx) -> Any`: View system prompt module status (bot owner only)
  - `clear_system_prompt_cache(ctx, guild_id: Optional[str]) -> Any`: Clear system prompt cache (bot owner only)

## Functions

### `setup(bot) -> Any`
設定函式，用於載入 Cog

