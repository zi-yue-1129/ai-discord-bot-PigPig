# File: `cogs/system_prompt/commands.py`

## Overview
This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `commands.py`, providing vital integrations within the PigPig bot ecosystem.
頻道系統提示管理模組的 Discord 斜線命令

提供完整的 Discord 斜線命令介面，包含所有系統提示管理功能。

## Classes

### `SystemPromptCommands`
系統提示管理命令類別

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.
  - `manager` (`Any`): Internal instance state.
  - `permission_validator` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: discord.Client) -> Any`: 初始化命令類別
  - `get_system_prompt_manager() -> SystemPromptManager`: 取得系統提示管理器實例
  - `system_prompt(interaction: discord.Interaction) -> Any`: 統一的系統提示管理命令 - 主選單介面
  - `set_personality(interaction: discord.Interaction, scope: app_commands.Choice[str], description: str) -> None`: Slash command to adjust bot personality via natural language description.

## Functions

### `handle_system_prompt_error(func: Any) -> Any`
系統提示錯誤處理裝飾器

### `setup(bot: Any) -> Any`
設定函式，用於載入 Cog


## Handwritten Context
# System Prompt System - Commands

**File:** [`cogs/system_prompt/commands.py`](cogs/system_prompt/commands.py)

The `SystemPromptCommands` cog provides the user-facing interface for the entire system prompt feature. It is designed around a single, unified slash command that uses Discord UI components for all interactions.

## `SystemPromptCommands` Class

### `__init__(self, bot)`

Initializes the command cog, creating instances of the `SystemPromptManager` and `PermissionValidator` to handle the backend logic and security.

### Main Command: `/system_prompt`

This is the sole entry point for users. Instead of having multiple commands for different actions, this command opens a main menu from which all other actions are launched.

*   **Behavior:** When executed, it creates and displays a `SystemPromptMainView` and a descriptive embed. All subsequent interactions happen through the buttons on this view. This approach simplifies the user experience and reduces the number of slash commands needed.

### UI-Driven Workflow

All functionality is handled through views and modals defined in `cogs/system_prompt/ui/`.

*   **`SystemPromptMainView`:** The main menu that appears when `/system_prompt` is run. It has buttons for:
    *   **Set Prompt:** Leads to a choice between setting the server or channel prompt, which then opens the `SystemPromptModal`.
    *   **View Config:** Shows the current effective prompt for the channel.
    *   **Edit Modules:** Opens a `ModuleSelectView` to allow editing specific YAML modules.
    *   **Copy Prompt:** Opens a `ChannelSelectView` to copy a prompt to another channel.
    *   **Remove Prompt:** Opens a confirmation view to delete a server or channel prompt.
*   **`SystemPromptModal`:** A popup form where users can type in the main prompt content and select modules to include.
*   **`ConfirmationView`:** A generic view with "Confirm" and "Cancel" buttons used for destructive actions like removing a prompt.

### Error Handling

The cog uses a decorator, `@handle_system_prompt_error`, on its main command. This wrapper catches all custom exceptions defined in `exceptions.py` (like `PermissionError`, `ValidationError`, `PromptNotFoundError`) and provides a consistent, user-friendly error message in an ephemeral response, preventing crashes and improving user feedback.