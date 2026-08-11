# File: `cogs/system_prompt/ui.py`

## Overview
頻道系統提示管理模組的 UI 元件

提供 Discord UI 元件，包含 Modal 對話框、確認按鈕、選擇器等。

## Classes

### `SystemPromptModal`
系統提示設定的 Modal 對話框

- **Attributes**:
  - `callback_func` (`Any`): Instance attribute managing callback_func.
  - `manager` (`Any`): Instance attribute managing manager.
  - `channel_id` (`Any`): Instance attribute managing channel_id.
  - `guild_id` (`Any`): Instance attribute managing guild_id.
  - `logger` (`Any`): Instance attribute managing logger.
  - `prompt_input` (`Any`): Instance attribute managing prompt_input.

- **Methods**:
  - `on_submit(interaction) -> Any`: 處理 Modal 提交
  - `on_error(interaction, error) -> Any`: 處理 Modal 錯誤

### `SystemPromptModuleModal`
模組設定的 Modal 對話框

- **Attributes**:
  - `module_name` (`Any`): Instance attribute managing module_name.
  - `callback_func` (`Any`): Instance attribute managing callback_func.
  - `manager` (`Any`): Instance attribute managing manager.
  - `module_description` (`Any`): Instance attribute managing module_description.
  - `logger` (`Any`): Instance attribute managing logger.
  - `module_input` (`Any`): Instance attribute managing module_input.

- **Methods**:
  - `on_submit(interaction) -> Any`: 處理模組 Modal 提交

### `ConfirmationView`
確認對話框 View

- **Attributes**:
  - `result` (`Any`): Instance attribute managing result.
  - `confirmed` (`Any`): Instance attribute managing confirmed.
  - `logger` (`Any`): Instance attribute managing logger.
  - `confirm_button` (`Any`): Instance attribute managing confirm_button.
  - `cancel_button` (`Any`): Instance attribute managing cancel_button.

- **Methods**:
  - `on_timeout() -> Any`: 處理超時

### `ChannelSelectView`
頻道選擇器 View

- **Attributes**:
  - `callback_func` (`Any`): Instance attribute managing callback_func.
  - `selected_channel` (`Any`): Instance attribute managing selected_channel.
  - `logger` (`Any`): Instance attribute managing logger.

### `ModuleSelectView`
模組選擇器 View

- **Attributes**:
  - `callback_func` (`Any`): Instance attribute managing callback_func.
  - `selected_modules` (`Any`): Instance attribute managing selected_modules.
  - `logger` (`Any`): Instance attribute managing logger.

### `SystemPromptView`
系統提示管理的主要 View

- **Attributes**:
  - `prompt_data` (`Any`): Instance attribute managing prompt_data.
  - `can_edit` (`Any`): Instance attribute managing can_edit.
  - `logger` (`Any`): Instance attribute managing logger.
  - `preview_button` (`Any`): Instance attribute managing preview_button.

- **Methods**:
  - `on_timeout() -> Any`: 處理超時

## Functions

### `create_system_prompt_embed(prompt_data, channel) -> discord.Embed`
建立系統提示的 Embed

Args:
    prompt_data: 提示資料
    channel: 頻道物件（可選）

Returns:
    Discord Embed 物件
