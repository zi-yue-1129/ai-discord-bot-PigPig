# File: `cogs/system_prompt/ui.py`

## Overview
頻道系統提示管理模組的 UI 元件

提供 Discord UI 元件，包含 Modal 對話框、確認按鈕、選擇器等。

## Classes

### `SystemPromptModal`
系統提示設定的 Modal 對話框

- **Attributes**:
  - `callback_func` (`Any`): Instance attribute for callback_func.
  - `manager` (`Any`): Instance attribute for manager.
  - `channel_id` (`Any`): Instance attribute for channel_id.
  - `guild_id` (`Any`): Instance attribute for guild_id.
  - `logger` (`Any`): Instance attribute for logger.
  - `prompt_input` (`Any`): Instance attribute for prompt_input.

- **Methods**:
  - `__init__(title, prompt_label, prompt_placeholder, initial_value, callback_func, manager, channel_id, guild_id, show_default_content, **kwargs) -> Any`: 初始化 Modal 對話框
  - `_restore_variable_placeholders(prompt, manager) -> str`: 還原變數占位符格式
  - `on_submit(interaction) -> Any`: 處理 Modal 提交
  - `on_error(interaction, error) -> Any`: 處理 Modal 錯誤

### `SystemPromptModuleModal`
模組設定的 Modal 對話框

- **Attributes**:
  - `module_name` (`Any`): Instance attribute for module_name.
  - `callback_func` (`Any`): Instance attribute for callback_func.
  - `manager` (`Any`): Instance attribute for manager.
  - `module_description` (`Any`): Instance attribute for module_description.
  - `logger` (`Any`): Instance attribute for logger.
  - `module_input` (`Any`): Instance attribute for module_input.

- **Methods**:
  - `__init__(module_name, initial_value, callback_func, manager, lang, show_default_content, **kwargs) -> Any`: 初始化模組設定 Modal
  - `on_submit(interaction) -> Any`: 處理模組 Modal 提交

### `ConfirmationView`
確認對話框 View

- **Attributes**:
  - `result` (`Any`): Instance attribute for result.
  - `confirmed` (`Any`): Instance attribute for confirmed.
  - `logger` (`Any`): Instance attribute for logger.
  - `confirm_button` (`Any`): Instance attribute for confirm_button.
  - `cancel_button` (`Any`): Instance attribute for cancel_button.

- **Methods**:
  - `__init__(confirm_text, cancel_text, confirm_style, timeout, **kwargs) -> Any`: 初始化確認對話框
  - `_confirm_callback(interaction) -> Any`: 確認按鈕回調
  - `_cancel_callback(interaction) -> Any`: 取消按鈕回調
  - `on_timeout() -> Any`: 處理超時

### `ChannelSelectView`
頻道選擇器 View

- **Attributes**:
  - `callback_func` (`Any`): Instance attribute for callback_func.
  - `selected_channel` (`Any`): Instance attribute for selected_channel.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(channels, placeholder, callback_func, timeout, **kwargs) -> Any`: 初始化頻道選擇器
  - `_select_callback(interaction) -> Any`: 選擇器回調

### `ModuleSelectView`
模組選擇器 View

- **Attributes**:
  - `callback_func` (`Any`): Instance attribute for callback_func.
  - `selected_modules` (`Any`): Instance attribute for selected_modules.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(modules, placeholder, callback_func, timeout, **kwargs) -> Any`: 初始化模組選擇器
  - `_select_callback(interaction) -> Any`: 模組選擇器回調

### `SystemPromptView`
系統提示管理的主要 View

- **Attributes**:
  - `prompt_data` (`Any`): Instance attribute for prompt_data.
  - `can_edit` (`Any`): Instance attribute for can_edit.
  - `logger` (`Any`): Instance attribute for logger.
  - `preview_button` (`Any`): Instance attribute for preview_button.

- **Methods**:
  - `__init__(prompt_data, can_edit, timeout, **kwargs) -> Any`: 初始化系統提示 View
  - `_edit_callback(interaction) -> Any`: 編輯按鈕回調
  - `_edit_modal_callback(interaction, new_prompt) -> Any`: 編輯 Modal 回調
  - `_preview_callback(interaction) -> Any`: 預覽按鈕回調
  - `on_timeout() -> Any`: 處理超時

## Functions

### `create_system_prompt_embed(prompt_data, channel) -> discord.Embed`
建立系統提示的 Embed
