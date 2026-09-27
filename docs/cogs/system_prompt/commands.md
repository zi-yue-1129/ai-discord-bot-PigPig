# File: `cogs/system_prompt/commands.py`

## Overview
頻道系統提示管理模組的 Discord 斜線命令

提供完整的 Discord 斜線命令介面，包含所有系統提示管理功能。

## Classes

### `SystemPromptCommands`
系統提示管理命令類別

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `logger` (`Any`): Instance attribute for logger.
  - `manager` (`Any`): Instance attribute for manager.
  - `permission_validator` (`Any`): Instance attribute for permission_validator.

- **Methods**:
  - `__init__(bot) -> Any`: 初始化命令類別
  - `get_system_prompt_manager() -> SystemPromptManager`: 取得系統提示管理器實例
  - `system_prompt(interaction) -> Any`: 統一的系統提示管理命令 - 主選單介面
  - `set_personality(interaction, scope, description) -> None`: Slash command to adjust bot personality via natural language description.

## Functions

### `handle_system_prompt_error(func) -> Any`
系統提示錯誤處理裝飾器

### `setup(bot) -> Any`
設定函式，用於載入 Cog
