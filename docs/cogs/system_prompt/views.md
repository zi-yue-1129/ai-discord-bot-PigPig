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
  - `manager` (`Any`): Instance attribute for manager.
  - `guild_id` (`Any`): Instance attribute for guild_id.
  - `_bot` (`Any`): Instance attribute for _bot.

- **Methods**:
  - `__init__(manager, guild_id, timeout) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__`.
  - `_t(*keys) -> str`: Translate *keys* using the guild's language.

### `SystemPromptMainView`
系統提示管理主選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute for permission_validator.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(manager, permission_validator, guild_id, timeout) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.
  - `_setup_main_buttons() -> Any`: 設定主要功能按鈕
  - `function_callback(interaction, function) -> Any`: 處理功能按鈕回調
  - `_handle_set_function(interaction) -> Any`: Handles the `_handle_set_function` functionality. Internally, it interacts with methods like `SystemPromptSetView` and `_ti`.
  - `_handle_view_function(interaction) -> Any`: Handles the `_handle_view_function` functionality. Internally, it interacts with methods like `SystemPromptViewOptionsView` and `_ti`.
  - `_handle_copy_function(interaction) -> Any`: Handles the `_handle_copy_function` functionality. Internally, it interacts with methods like `SystemPromptCopyView` and `_ti`.
  - `_handle_remove_function(interaction) -> Any`: Handles the `_handle_remove_function` functionality. Internally, it interacts with methods like `SystemPromptRemoveView` and `_ti`.
  - `_handle_reset_function(interaction) -> Any`: Handles the `_handle_reset_function` functionality. Internally, it interacts with methods like `SystemPromptResetView` and `_ti`.
  - `_handle_reload_function(interaction) -> Any`: Handles the `_handle_reload_function` functionality. Internally, it interacts with methods like `callable` and `iscoroutinefunction`.

### `SystemPromptFunctionButton`
系統提示功能按鈕

- **Attributes**:
  - `function` (`Any`): Instance attribute for function.

- **Methods**:
  - `__init__(function, **kwargs) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__`.
  - `callback(interaction) -> Any`: 按鈕回調

### `SystemPromptSetView`
設定系統提示的子選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute for permission_validator.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(manager, permission_validator, guild_id, timeout) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.
  - `scope_callback(interaction, scope) -> Any`: Handles the `scope_callback` functionality. Internally, it interacts with methods like `EditModeSelectionView` and `_ti`.

### `EditModeSelectionView`
編輯模式選擇選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute for permission_validator.
  - `scope` (`Any`): Instance attribute for scope.
  - `target_channel` (`Any`): Instance attribute for target_channel.
  - `scope_text` (`Any`): Instance attribute for scope_text.
  - `guild` (`Any`): Instance attribute for guild.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(manager, permission_validator, scope, target_channel, scope_text, guild, guild_id, timeout) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.
  - `edit_mode_callback(interaction, edit_mode) -> Any`: 處理編輯模式選擇
  - `_handle_direct_edit(interaction) -> Any`: 處理直接編輯提示
  - `_restore_variable_placeholders(prompt, guild_id) -> str`: 將已替換的變數還原為占位符格式，以便編輯時顯示原始模板
  - `_handle_module_edit(interaction) -> Any`: 處理模組化編輯
  - `_handle_direct_set_callback(interaction, content) -> Any`: 處理直接設定回調

### `EditModeButton`
編輯模式按鈕

- **Attributes**:
  - `edit_mode` (`Any`): Instance attribute for edit_mode.

- **Methods**:
  - `__init__(edit_mode, **kwargs) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__`.
  - `callback(interaction) -> Any`: Handles the `callback` functionality. Internally, it interacts with methods like `edit_mode_callback` and `send_message`.

### `SystemPromptScopeButton`
範圍選擇按鈕

- **Attributes**:
  - `scope` (`Any`): Instance attribute for scope.

- **Methods**:
  - `__init__(scope, **kwargs) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__`.
  - `callback(interaction) -> Any`: Handles the `callback` functionality. Internally, it interacts with methods like `scope_callback` and `send_message`.

### `SystemPromptViewOptionsView`
查看配置選項選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute for permission_validator.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(manager, permission_validator, guild_id, timeout) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.
  - `view_callback(interaction, view_type) -> Any`: 處理查看回調

### `SystemPromptViewButton`
查看選項按鈕

- **Attributes**:
  - `view_type` (`Any`): Instance attribute for view_type.

- **Methods**:
  - `__init__(view_type, **kwargs) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__`.
  - `callback(interaction) -> Any`: Handles the `callback` functionality. Internally, it interacts with methods like `view_callback` and `send_message`.

### `ModuleEditView`
Represents the `ModuleEditView` class in the system.

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute for permission_validator.
  - `modules` (`Any`): Instance attribute for modules.
  - `guild` (`Any`): Instance attribute for guild.
  - `scope` (`Any`): Instance attribute for scope.
  - `target_channel` (`Any`): Instance attribute for target_channel.
  - `scope_text` (`Any`): Instance attribute for scope_text.
  - `logger` (`Any`): Instance attribute for logger.
  - `selected_scope` (`Any`): Instance attribute for selected_scope.

- **Methods**:
  - `__init__(manager, permission_validator, modules, guild, scope, target_channel, scope_text, guild_id, timeout) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.
  - `_setup_scope_selector() -> Any`: Handles the `_setup_scope_selector` functionality. Internally, it interacts with methods like `clear_items` and `add_item`.
  - `_setup_module_selector() -> Any`: Handles the `_setup_module_selector` functionality. Internally, it interacts with methods like `clear_items` and `_t`.
  - `scope_callback(interaction, scope) -> Any`: Handles the `scope_callback` functionality. Internally, it interacts with methods like `get_available_modules` and `_setup_module_selector`.

### `ModuleScopeButton`
模組範圍選擇按鈕

- **Attributes**:
  - `scope` (`Any`): Instance attribute for scope.

- **Methods**:
  - `__init__(scope, **kwargs) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__`.
  - `callback(interaction) -> Any`: Handles the `callback` functionality. Internally, it interacts with methods like `scope_callback` and `send_message`.

### `ModuleSelect`
模組選擇器

- **Attributes**:
  - `manager` (`Any`): Instance attribute for manager.
  - `scope` (`Any`): Instance attribute for scope.
  - `channel` (`Any`): Instance attribute for channel.
  - `guild` (`Any`): Instance attribute for guild.
  - `scope_text` (`Any`): Instance attribute for scope_text.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(manager, scope, channel, guild, scope_text, **kwargs) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.
  - `_update_option_descriptions() -> Any`: 更新選項的說明文字 (基於語言管理器)
  - `callback(interaction) -> Any`: 選擇器回調
  - `_handle_module_callback(interaction, module_name, content) -> Any`: 處理模組編輯回調

### `SystemPromptCopyView`
複製系統提示選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute for permission_validator.
  - `guild` (`Any`): Instance attribute for guild.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(manager, permission_validator, guild, guild_id, timeout) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.

### `SystemPromptRemoveView`
移除系統提示的子選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute for permission_validator.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(manager, permission_validator, guild_id, timeout) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.

### `SystemPromptResetView`
重置系統提示的子選單

- **Attributes**:
  - `permission_validator` (`Any`): Instance attribute for permission_validator.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(manager, permission_validator, guild_id, timeout) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.

### `BackButton`
返回主選單按鈕

- **Attributes**:
  - `guild_id` (`str`): Instance attribute for guild_id.
  - `_bot` (`Any`): Instance attribute for _bot.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(row, guild_id, bot) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.
  - `callback(interaction) -> Any`: 返回主選單

### `ChannelSelect`
頻道選擇器（用於複製功能）

- **Attributes**:
  - `selected_channel_id` (`Optional[...]`): Instance attribute for selected_channel_id.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(**kwargs) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.
  - `callback(interaction) -> Any`: Handles the `callback` functionality. Internally, it interacts with methods like `debug` and `edit_message`.

### `CopyExecuteButton`
執行複製按鈕

- **Attributes**:
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(label, **kwargs) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.
  - `callback(interaction) -> Any`: Handles the `callback` functionality. Internally, it interacts with methods like `get` and `error`.

### `RemoveButton`
移除按鈕

- **Attributes**:
  - `remove_type` (`Any`): Instance attribute for remove_type.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(label, remove_type, **kwargs) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.
  - `callback(interaction) -> Any`: Handles the `callback` functionality. Internally, it interacts with methods like `error` and `Embed`.

### `ResetButton`
重置按鈕

- **Attributes**:
  - `reset_type` (`Any`): Instance attribute for reset_type.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(label, reset_type, **kwargs) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__` and `get_logger`.
  - `callback(interaction) -> Any`: Handles the `callback` functionality. Internally, it interacts with methods like `error` and `_load_guild_config`.

## Functions

### `_ti(interaction, *keys) -> str`
Translate a key using the guild language from an interaction context.
