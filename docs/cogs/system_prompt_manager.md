# File: `cogs/system_prompt_manager.py`

## Overview
This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `system_prompt_manager.py`, providing vital integrations within the PigPig bot ecosystem.
頻道系統提示管理模組的主要 Cog

這個檔案作為系統提示管理模組的入口點，整合所有功能組件。

## Classes

### `SystemPromptManagerCog`
系統提示管理主要 Cog 類別

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.
  - `manager` (`Any`): Internal instance state.
  - `permission_validator` (`Any`): Internal instance state.
  - `commands_cog` (`Any`): Internal instance state.
  - `language_manager` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: commands.Bot) -> Any`: 初始化系統提示管理 Cog
  - `_get_language_manager() -> Any`: 安全地取得語言管理器實例
  - `_translate(guild_id: str) -> Any`: 安全的翻譯方法，使用 getattr 避免類型檢查問題
  - `cog_load() -> Any`: Cog 載入時的初始化
  - `cog_unload() -> Any`: Cog 卸載時的清理
  - `get_system_prompt_manager() -> SystemPromptManager`: 取得系統提示管理器實例
  - `get_permission_validator() -> PermissionValidator`: 取得權限驗證器實例
  - `get_effective_system_prompt(channel_id: str, guild_id: str, message: Optional[discord.Message]) -> str`: 取得有效的系統提示（供外部模組調用的便利方法）
  - `validate_user_permission(user: discord.Member, action: str, target: any) -> bool`: 驗證用戶權限（供外部模組調用的便利方法）
  - `on_guild_join(guild: discord.Guild) -> Any`: 當機器人加入新伺服器時的處理
  - `on_guild_remove(guild: discord.Guild) -> Any`: 當機器人離開伺服器時的處理
  - `system_prompt_status(ctx: Any) -> Any`: View system prompt module status (bot owner only)
  - `clear_system_prompt_cache(ctx: Any, guild_id: Optional[str]) -> Any`: Clear system prompt cache (bot owner only)

## Functions

### `setup(bot: Any) -> Any`
設定函式，用於載入 Cog


## Handwritten Context
# System Prompt Manager Cog

**File:** [`cogs/system_prompt_manager.py`](cogs/system_prompt_manager.py)

This cog serves as the central coordinator for the powerful System Prompt management feature. It acts as the main entry point, loading and integrating all the necessary components from the `cogs/system_prompt/` directory.

## Dependencies

This cog is the primary interface for the **[System Prompt System](./system_prompt/index.md)**. It initializes and provides access to the core components of this system, including:

*   **`SystemPromptManager`:** The core engine that handles the logic of storing, retrieving, and combining prompts.
*   **`SystemPromptCommands`:** The cog that contains all the user-facing slash commands for managing prompts.
*   **`PermissionValidator`:** The component responsible for checking if a user has the required permissions to manage prompts.

## Role as a Coordinator

The `SystemPromptManagerCog` itself does not contain any user-facing commands. Its main responsibilities are:

1.  **Initialization:** It creates instances of the `SystemPromptManager`, `PermissionValidator`, and `SystemPromptCommands` cog.
2.  **Cog Loading:** It ensures that the `SystemPromptCommands` cog is properly loaded into the bot, making the slash commands available to users.
3.  **Central Access Point:** It provides getter methods (`get_system_prompt_manager`, `get_permission_validator`) for other parts of the bot (like the core message handler) to easily access the system's functionality.
4.  **Convenience Methods:** It offers high-level methods like `get_effective_system_prompt` that simplify the process for external modules to get the final, combined system prompt for a specific channel.

## Owner-only Commands

This cog also includes two hidden commands for the bot owner to manage the module itself:

*   `/system_prompt_status`: Displays the status of the module, including cache size and loaded components.
*   `/system_prompt_clear_cache`: Allows the owner to clear the prompt cache for a specific server or for all servers.