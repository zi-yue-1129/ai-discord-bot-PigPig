# File: `cogs/system_prompt/ui.py`

## Overview
頻道系統提示管理模組的 UI 元件

提供 Discord UI 元件，包含 Modal 對話框、確認按鈕、選擇器等。

## Classes

### `SystemPromptModal`
系統提示設定的 Modal 對話框

- **Attributes**:
  - `callback_func` (`Any`): Instance attribute callback_func
  - `manager` (`Any`): Instance attribute manager
  - `channel_id` (`Any`): Instance attribute channel_id
  - `guild_id` (`Any`): Instance attribute guild_id
  - `logger` (`Any`): Instance attribute logger
  - `prompt_input` (`Any`): Instance attribute prompt_input

- **Methods**:
  - `_restore_variable_placeholders(self, prompt, manager) -> str`: 還原變數占位符格式  Args:     prompt: 已替換變數的提示     manager: SystemPromptManager 實例      Returns:     還原變數占位符的提示
  - `on_submit(self, interaction) -> Any`: 處理 Modal 提交
  - `on_error(self, interaction, error) -> Any`: 處理 Modal 錯誤

### `SystemPromptModuleModal`
模組設定的 Modal 對話框

- **Attributes**:
  - `module_name` (`Any`): Instance attribute module_name
  - `callback_func` (`Any`): Instance attribute callback_func
  - `manager` (`Any`): Instance attribute manager
  - `module_description` (`Any`): Instance attribute module_description
  - `logger` (`Any`): Instance attribute logger
  - `module_input` (`Any`): Instance attribute module_input
  - `description_display` (`Any`): Instance attribute description_display

- **Methods**:
  - `on_submit(self, interaction) -> Any`: 處理模組 Modal 提交

### `ConfirmationView`
確認對話框 View

- **Attributes**:
  - `result` (`Any`): Instance attribute result
  - `confirmed` (`Any`): Instance attribute confirmed
  - `logger` (`Any`): Instance attribute logger
  - `confirm_button` (`Any`): Instance attribute confirm_button
  - `cancel_button` (`Any`): Instance attribute cancel_button

- **Methods**:
  - `_confirm_callback(self, interaction) -> Any`: 確認按鈕回調
  - `_cancel_callback(self, interaction) -> Any`: 取消按鈕回調
  - `on_timeout(self) -> Any`: 處理超時

### `ChannelSelectView`
頻道選擇器 View

- **Attributes**:
  - `callback_func` (`Any`): Instance attribute callback_func
  - `selected_channel` (`Any`): Instance attribute selected_channel
  - `logger` (`Any`): Instance attribute logger
  - `channel_select` (`Any`): Instance attribute channel_select

- **Methods**:
  - `_select_callback(self, interaction) -> Any`: 選擇器回調

### `ModuleSelectView`
模組選擇器 View

- **Attributes**:
  - `callback_func` (`Any`): Instance attribute callback_func
  - `selected_modules` (`Any`): Instance attribute selected_modules
  - `logger` (`Any`): Instance attribute logger
  - `module_select` (`Any`): Instance attribute module_select

- **Methods**:
  - `_select_callback(self, interaction) -> Any`: 模組選擇器回調

### `SystemPromptView`
系統提示管理的主要 View

- **Attributes**:
  - `prompt_data` (`Any`): Instance attribute prompt_data
  - `can_edit` (`Any`): Instance attribute can_edit
  - `logger` (`Any`): Instance attribute logger
  - `preview_button` (`Any`): Instance attribute preview_button
  - `edit_button` (`Any`): Instance attribute edit_button

- **Methods**:
  - `_edit_callback(self, interaction) -> Any`: 編輯按鈕回調
  - `_edit_modal_callback(self, interaction, new_prompt) -> Any`: 編輯 Modal 回調
  - `_preview_callback(self, interaction) -> Any`: 預覽按鈕回調
  - `on_timeout(self) -> Any`: 處理超時

## Functions

### `create_system_prompt_embed(prompt_data, channel) -> discord.Embed`
建立系統提示的 Embed  Args:     prompt_data: 提示資料     channel: 頻道物件（可選）      Returns:     Discord Embed 物件
