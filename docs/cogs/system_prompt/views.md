# File: `cogs/system_prompt/views.py`

## Overview
系統提示管理的統一 UI 選單系統

提供全新的統一介面，整合所有系統提示管理功能和模組化編輯。

## Classes

### `LocalizedView`
Base class for all system-prompt views.

Provides :meth:`_t` for translating strings at construction time using
the server's configured language.

- **Attributes**:
  - `manager` (`Any`): Instance attribute managing manager.
  - `guild_id` (`Any`): Instance attribute managing guild_id.
  - `_bot` (`Any`): Instance attribute managing _bot.

### `SystemPromptMainView`
系統提示管理主選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute managing permission_validator.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `function_callback(interaction, function) -> Any`: 處理功能按鈕回調

### `SystemPromptFunctionButton`
系統提示功能按鈕

- **Attributes**:
  - `function` (`Any`): Instance attribute managing function.

- **Methods**:
  - `callback(interaction) -> Any`: 按鈕回調

### `SystemPromptSetView`
設定系統提示的子選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute managing permission_validator.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `scope_callback(interaction, scope) -> Any`: Executes scope_callback operation.

### `EditModeSelectionView`
編輯模式選擇選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute managing permission_validator.
  - `scope` (`Any`): Instance attribute managing scope.
  - `target_channel` (`Any`): Instance attribute managing target_channel.
  - `scope_text` (`Any`): Instance attribute managing scope_text.
  - `guild` (`Any`): Instance attribute managing guild.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `edit_mode_callback(interaction, edit_mode) -> Any`: 處理編輯模式選擇

### `EditModeButton`
編輯模式按鈕

- **Attributes**:
  - `edit_mode` (`Any`): Instance attribute managing edit_mode.

- **Methods**:
  - `callback(interaction) -> Any`: 按鈕回調

### `SystemPromptScopeButton`
範圍選擇按鈕

- **Attributes**:
  - `scope` (`Any`): Instance attribute managing scope.

- **Methods**:
  - `callback(interaction) -> Any`: 按鈕回調

### `SystemPromptViewOptionsView`
查看配置選項選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute managing permission_validator.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `view_callback(interaction, view_type) -> Any`: 處理查看回調

### `SystemPromptViewButton`
查看選項按鈕

- **Attributes**:
  - `view_type` (`Any`): Instance attribute managing view_type.

- **Methods**:
  - `callback(interaction) -> Any`: 按鈕回調

### `ModuleEditView`
Represents ModuleEditView.

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute managing permission_validator.
  - `modules` (`Any`): Instance attribute managing modules.
  - `guild` (`Any`): Instance attribute managing guild.
  - `scope` (`Any`): Instance attribute managing scope.
  - `target_channel` (`Any`): Instance attribute managing target_channel.
  - `scope_text` (`Any`): Instance attribute managing scope_text.
  - `logger` (`Any`): Instance attribute managing logger.
  - `selected_scope` (`Any`): Instance attribute managing selected_scope.

- **Methods**:
  - `scope_callback(interaction, scope) -> Any`: Executes scope_callback operation.

### `ModuleScopeButton`
模組範圍選擇按鈕

- **Attributes**:
  - `scope` (`Any`): Instance attribute managing scope.

- **Methods**:
  - `callback(interaction) -> Any`: 按鈕回調

### `ModuleSelect`
模組選擇器

- **Attributes**:
  - `manager` (`Any`): Instance attribute managing manager.
  - `scope` (`Any`): Instance attribute managing scope.
  - `channel` (`Any`): Instance attribute managing channel.
  - `guild` (`Any`): Instance attribute managing guild.
  - `scope_text` (`Any`): Instance attribute managing scope_text.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `callback(interaction) -> Any`: 選擇器回調

### `SystemPromptCopyView`
複製系統提示選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute managing permission_validator.
  - `guild` (`Any`): Instance attribute managing guild.
  - `logger` (`Any`): Instance attribute managing logger.

### `SystemPromptRemoveView`
移除系統提示的子選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute managing permission_validator.
  - `logger` (`Any`): Instance attribute managing logger.

### `SystemPromptResetView`
重置系統提示的子選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute managing permission_validator.
  - `logger` (`Any`): Instance attribute managing logger.

### `BackButton`
返回主選單按鈕

- **Attributes**:
  - `_bot` (`Any`): Instance attribute managing _bot.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `callback(interaction) -> Any`: 返回主選單

### `ChannelSelect`
頻道選擇器（用於複製功能）

- **Attributes**:
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `callback(interaction) -> Any`: 按鈕回調

### `CopyExecuteButton`
執行複製按鈕

- **Attributes**:
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `callback(interaction) -> Any`: 按鈕回調

### `RemoveButton`
移除按鈕

- **Attributes**:
  - `remove_type` (`Any`): Instance attribute managing remove_type.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `callback(interaction) -> Any`: 按鈕回調

### `ResetButton`
重置按鈕

- **Attributes**:
  - `reset_type` (`Any`): Instance attribute managing reset_type.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `callback(interaction) -> Any`: 按鈕回調
