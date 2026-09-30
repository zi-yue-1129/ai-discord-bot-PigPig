# File: `cogs/system_prompt/views.py`

## Overview
系統提示管理的統一 UI 選單系統

提供全新的統一介面，整合所有系統提示管理功能和模組化編輯。

## Classes

### `LocalizedView`
Base class for all system-prompt views.  Provides :meth:`_t` for translating strings at construction time using the server's configured language.

- **Attributes**:
  - `manager` (`Any`): Instance attribute manager
  - `guild_id` (`Any`): Instance attribute guild_id
  - `_bot` (`Any`): Instance attribute _bot

- **Methods**:
  - `_t(self, *keys) -> str`: Translate *keys* using the guild's language.  Falls back to ``fallback`` (or the last key segment) when LanguageManager is unavailable or the key is missing.

### `SystemPromptMainView`
系統提示管理主選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute permission_validator
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `_setup_main_buttons(self) -> Any`: 設定主要功能按鈕
  - `function_callback(self, interaction, function) -> Any`: 處理功能按鈕回調
  - `_handle_set_function(self, interaction) -> Any`: Method _handle_set_function.
  - `_handle_view_function(self, interaction) -> Any`: Method _handle_view_function.
  - `_handle_copy_function(self, interaction) -> Any`: Method _handle_copy_function.
  - `_handle_remove_function(self, interaction) -> Any`: Method _handle_remove_function.
  - `_handle_reset_function(self, interaction) -> Any`: Method _handle_reset_function.
  - `_handle_reload_function(self, interaction) -> Any`: Method _handle_reload_function.

### `SystemPromptFunctionButton`
系統提示功能按鈕

- **Attributes**:
  - `function` (`Any`): Instance attribute function

- **Methods**:
  - `callback(self, interaction) -> Any`: 按鈕回調

### `SystemPromptSetView`
設定系統提示的子選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute permission_validator
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `scope_callback(self, interaction, scope) -> Any`: Method scope_callback.

### `EditModeSelectionView`
編輯模式選擇選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute permission_validator
  - `scope` (`Any`): Instance attribute scope
  - `target_channel` (`Any`): Instance attribute target_channel
  - `scope_text` (`Any`): Instance attribute scope_text
  - `guild` (`Any`): Instance attribute guild
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `edit_mode_callback(self, interaction, edit_mode) -> Any`: 處理編輯模式選擇
  - `_handle_direct_edit(self, interaction) -> Any`: 處理直接編輯提示
  - `_restore_variable_placeholders(self, prompt, guild_id) -> str`: 將已替換的變數還原為占位符格式，以便編輯時顯示原始模板  Args:     prompt: 已替換變數的提示     guild_id: 伺服器 ID      Returns:     還原變數占位符的提示
  - `_handle_module_edit(self, interaction) -> Any`: 處理模組化編輯
  - `_handle_direct_set_callback(self, interaction, content) -> Any`: 處理直接設定回調

### `EditModeButton`
編輯模式按鈕

- **Attributes**:
  - `edit_mode` (`Any`): Instance attribute edit_mode

- **Methods**:
  - `callback(self, interaction) -> Any`: Method callback.

### `SystemPromptScopeButton`
範圍選擇按鈕

- **Attributes**:
  - `scope` (`Any`): Instance attribute scope

- **Methods**:
  - `callback(self, interaction) -> Any`: Method callback.

### `SystemPromptViewOptionsView`
查看配置選項選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute permission_validator
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `view_callback(self, interaction, view_type) -> Any`: 處理查看回調

### `SystemPromptViewButton`
查看選項按鈕

- **Attributes**:
  - `view_type` (`Any`): Instance attribute view_type

- **Methods**:
  - `callback(self, interaction) -> Any`: Method callback.

### `ModuleEditView`
Class representing ModuleEditView.

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute permission_validator
  - `modules` (`Any`): Instance attribute modules
  - `guild` (`Any`): Instance attribute guild
  - `scope` (`Any`): Instance attribute scope
  - `target_channel` (`Any`): Instance attribute target_channel
  - `scope_text` (`Any`): Instance attribute scope_text
  - `logger` (`Any`): Instance attribute logger
  - `selected_scope` (`Any`): Instance attribute selected_scope

- **Methods**:
  - `_setup_scope_selector(self) -> Any`: Method _setup_scope_selector.
  - `_setup_module_selector(self) -> Any`: Method _setup_module_selector.
  - `scope_callback(self, interaction, scope) -> Any`: Method scope_callback.

### `ModuleScopeButton`
模組範圍選擇按鈕

- **Attributes**:
  - `scope` (`Any`): Instance attribute scope

- **Methods**:
  - `callback(self, interaction) -> Any`: Method callback.

### `ModuleSelect`
模組選擇器

- **Attributes**:
  - `manager` (`Any`): Instance attribute manager
  - `scope` (`Any`): Instance attribute scope
  - `channel` (`Any`): Instance attribute channel
  - `guild` (`Any`): Instance attribute guild
  - `scope_text` (`Any`): Instance attribute scope_text
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `_update_option_descriptions(self) -> Any`: 更新選項的說明文字 (基於語言管理器)
  - `callback(self, interaction) -> Any`: 選擇器回調
  - `_handle_module_callback(self, interaction, module_name, content) -> Any`: 處理模組編輯回調

### `SystemPromptCopyView`
複製系統提示選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute permission_validator
  - `guild` (`Any`): Instance attribute guild
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - None

### `SystemPromptRemoveView`
移除系統提示的子選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute permission_validator
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - None

### `SystemPromptResetView`
重置系統提示的子選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute permission_validator
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - None

### `BackButton`
返回主選單按鈕

- **Attributes**:
  - `guild_id` (`str`): Instance attribute guild_id
  - `_bot` (`Any`): Instance attribute _bot
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `callback(self, interaction) -> Any`: 返回主選單

### `ChannelSelect`
頻道選擇器（用於複製功能）

- **Attributes**:
  - `selected_channel_id` (`Optional[str]`): Instance attribute selected_channel_id
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `callback(self, interaction) -> Any`: Method callback.

### `CopyExecuteButton`
執行複製按鈕

- **Attributes**:
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `callback(self, interaction) -> Any`: Method callback.

### `RemoveButton`
移除按鈕

- **Attributes**:
  - `remove_type` (`Any`): Instance attribute remove_type
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `callback(self, interaction) -> Any`: Method callback.

### `ResetButton`
重置按鈕

- **Attributes**:
  - `reset_type` (`Any`): Instance attribute reset_type
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `callback(self, interaction) -> Any`: Method callback.

## Functions

### `_ti(interaction, *keys) -> str`
Translate a key using the guild language from an interaction context.  Falls back to ``fallback`` (or the last key segment) when LanguageManager is unavailable or the key is missing.
