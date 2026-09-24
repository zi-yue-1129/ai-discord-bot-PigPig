# File: `cogs/system_prompt/commands.py`

## Overview
頻道系統提示管理模組的 Discord 斜線命令

## Classes

### `SystemPromptCommands`
系統提示管理命令類別

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: discord.Client) -> Any`: 初始化命令類別
  - `get_system_prompt_manager() -> SystemPromptManager`: 取得系統提示管理器實例
  - `system_prompt(interaction: discord.Interaction) -> Any`: 統一的系統提示管理命令 - 主選單介面
  - `set_personality(interaction: discord.Interaction, scope: app_commands.Choice[str], description: str) -> None`: Slash command to adjust bot personality via natural language description.

## Functions

### `handle_system_prompt_error(func) -> Any`
系統提示錯誤處理裝飾器

### `setup(bot) -> Any`
設定函式，用於載入 Cog

