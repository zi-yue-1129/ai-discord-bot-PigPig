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
  - `manager` (`Any`): Attribute holding manager data.
  - `guild_id` (`Any`): Attribute holding guild_id data.
  - `_bot` (`Any`): Attribute holding _bot data.

- **Methods**:
  - `__init__(manager: SystemPromptManager, guild_id: str, timeout: float) -> Any`: Executes __init__ logic.
  - `_t(*keys, fallback: str) -> str`: Translate *keys* using the guild's language.

### `SystemPromptMainView`
系統提示管理主選單

- **Attributes**:
  - `permission_validator` (`Any`): Attribute holding permission_validator data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, guild_id: str, timeout: float) -> Any`: Executes __init__ logic.
  - `_setup_main_buttons() -> Any`: 設定主要功能按鈕
  - `function_callback(interaction: discord.Interaction, function: str) -> Any`: 處理功能按鈕回調
  - `_handle_set_function(interaction: discord.Interaction) -> Any`: Executes _handle_set_function logic.
  - `_handle_view_function(interaction: discord.Interaction) -> Any`: Executes _handle_view_function logic.
  - `_handle_copy_function(interaction: discord.Interaction) -> Any`: Executes _handle_copy_function logic.
  - `_handle_remove_function(interaction: discord.Interaction) -> Any`: Executes _handle_remove_function logic.
  - `_handle_reset_function(interaction: discord.Interaction) -> Any`: Executes _handle_reset_function logic.
  - `_handle_reload_function(interaction: discord.Interaction) -> Any`: Executes _handle_reload_function logic.

### `SystemPromptFunctionButton`
系統提示功能按鈕

- **Attributes**:
  - `function` (`Any`): Attribute holding function data.

- **Methods**:
  - `__init__(function: str, **kwargs) -> Any`: Executes __init__ logic.
  - `callback(interaction: discord.Interaction) -> Any`: 按鈕回調

### `SystemPromptSetView`
設定系統提示的子選單

- **Attributes**:
  - `permission_validator` (`Any`): Attribute holding permission_validator data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, guild_id: str, timeout: float) -> Any`: Executes __init__ logic.
  - `scope_callback(interaction: discord.Interaction, scope: str) -> Any`: Executes scope_callback logic.

### `EditModeSelectionView`
編輯模式選擇選單

- **Attributes**:
  - `permission_validator` (`Any`): Attribute holding permission_validator data.
  - `scope` (`Any`): Attribute holding scope data.
  - `target_channel` (`Any`): Attribute holding target_channel data.
  - `scope_text` (`Any`): Attribute holding scope_text data.
  - `guild` (`Any`): Attribute holding guild data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, scope: str, target_channel: Optional[discord.TextChannel], scope_text: str, guild: discord.Guild, guild_id: str, timeout: float) -> Any`: Executes __init__ logic.
  - `edit_mode_callback(interaction: discord.Interaction, edit_mode: str) -> Any`: 處理編輯模式選擇
  - `_handle_direct_edit(interaction: discord.Interaction) -> Any`: 處理直接編輯提示
  - `_restore_variable_placeholders(prompt: str, guild_id: str) -> str`: 將已替換的變數還原為占位符格式，以便編輯時顯示原始模板
  - `_handle_module_edit(interaction: discord.Interaction) -> Any`: 處理模組化編輯
  - `_handle_direct_set_callback(interaction: discord.Interaction, content: str) -> Any`: 處理直接設定回調

### `EditModeButton`
編輯模式按鈕

- **Attributes**:
  - `edit_mode` (`Any`): Attribute holding edit_mode data.

- **Methods**:
  - `__init__(edit_mode: str, **kwargs) -> Any`: Executes __init__ logic.
  - `callback(interaction: discord.Interaction) -> Any`: Executes callback logic.

### `SystemPromptScopeButton`
範圍選擇按鈕

- **Attributes**:
  - `scope` (`Any`): Attribute holding scope data.

- **Methods**:
  - `__init__(scope: str, **kwargs) -> Any`: Executes __init__ logic.
  - `callback(interaction: discord.Interaction) -> Any`: Executes callback logic.

### `SystemPromptViewOptionsView`
查看配置選項選單

- **Attributes**:
  - `permission_validator` (`Any`): Attribute holding permission_validator data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, guild_id: str, timeout: float) -> Any`: Executes __init__ logic.
  - `view_callback(interaction: discord.Interaction, view_type: str) -> Any`: 處理查看回調

### `SystemPromptViewButton`
查看選項按鈕

- **Attributes**:
  - `view_type` (`Any`): Attribute holding view_type data.

- **Methods**:
  - `__init__(view_type: str, **kwargs) -> Any`: Executes __init__ logic.
  - `callback(interaction: discord.Interaction) -> Any`: Executes callback logic.

### `ModuleEditView`
Core class implementation.

- **Attributes**:
  - `permission_validator` (`Any`): Attribute holding permission_validator data.
  - `modules` (`Any`): Attribute holding modules data.
  - `guild` (`Any`): Attribute holding guild data.
  - `scope` (`Any`): Attribute holding scope data.
  - `target_channel` (`Any`): Attribute holding target_channel data.
  - `scope_text` (`Any`): Attribute holding scope_text data.
  - `logger` (`Any`): Attribute holding logger data.
  - `selected_scope` (`Any`): Attribute holding selected_scope data.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, modules: List[str], guild: discord.Guild, scope: Optional[str], target_channel: Optional[discord.TextChannel], scope_text: Optional[str], guild_id: str, timeout: float) -> Any`: Executes __init__ logic.
  - `_setup_scope_selector() -> Any`: Executes _setup_scope_selector logic.
  - `_setup_module_selector() -> Any`: Executes _setup_module_selector logic.
  - `scope_callback(interaction: discord.Interaction, scope: str) -> Any`: Executes scope_callback logic.

### `ModuleScopeButton`
模組範圍選擇按鈕

- **Attributes**:
  - `scope` (`Any`): Attribute holding scope data.

- **Methods**:
  - `__init__(scope: str, **kwargs) -> Any`: Executes __init__ logic.
  - `callback(interaction: discord.Interaction) -> Any`: Executes callback logic.

### `ModuleSelect`
模組選擇器

- **Attributes**:
  - `manager` (`Any`): Attribute holding manager data.
  - `scope` (`Any`): Attribute holding scope data.
  - `channel` (`Any`): Attribute holding channel data.
  - `guild` (`Any`): Attribute holding guild data.
  - `scope_text` (`Any`): Attribute holding scope_text data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(manager: SystemPromptManager, scope: str, channel: Optional[discord.TextChannel], guild: discord.Guild, scope_text: Optional[str], **kwargs) -> Any`: Executes __init__ logic.
  - `_update_option_descriptions() -> Any`: 更新選項的說明文字 (基於語言管理器)
  - `callback(interaction: discord.Interaction) -> Any`: 選擇器回調
  - `_handle_module_callback(interaction: discord.Interaction, module_name: str, content: str) -> Any`: 處理模組編輯回調

### `SystemPromptCopyView`
複製系統提示選單

- **Attributes**:
  - `permission_validator` (`Any`): Attribute holding permission_validator data.
  - `guild` (`Any`): Attribute holding guild data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, guild: discord.Guild, guild_id: str, timeout: float) -> Any`: Executes __init__ logic.

### `SystemPromptRemoveView`
移除系統提示的子選單

- **Attributes**:
  - `permission_validator` (`Any`): Attribute holding permission_validator data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, guild_id: str, timeout: float) -> Any`: Executes __init__ logic.

### `SystemPromptResetView`
重置系統提示的子選單

- **Attributes**:
  - `permission_validator` (`Any`): Attribute holding permission_validator data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, guild_id: str, timeout: float) -> Any`: Executes __init__ logic.

### `BackButton`
返回主選單按鈕

- **Attributes**:
  - `guild_id` (`str`): Attribute holding guild_id data.
  - `_bot` (`Any`): Attribute holding _bot data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(row: int, guild_id: str, bot) -> Any`: Executes __init__ logic.
  - `callback(interaction: discord.Interaction) -> Any`: 返回主選單

### `ChannelSelect`
頻道選擇器（用於複製功能）

- **Attributes**:
  - `selected_channel_id` (`Optional[str]`): Attribute holding selected_channel_id data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(**kwargs) -> Any`: Executes __init__ logic.
  - `callback(interaction: discord.Interaction) -> Any`: Executes callback logic.

### `CopyExecuteButton`
執行複製按鈕

- **Attributes**:
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(label: str, **kwargs) -> Any`: Executes __init__ logic.
  - `callback(interaction: discord.Interaction) -> Any`: Executes callback logic.

### `RemoveButton`
移除按鈕

- **Attributes**:
  - `remove_type` (`Any`): Attribute holding remove_type data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(label: str, remove_type: str, **kwargs) -> Any`: Executes __init__ logic.
  - `callback(interaction: discord.Interaction) -> Any`: Executes callback logic.

### `ResetButton`
重置按鈕

- **Attributes**:
  - `reset_type` (`Any`): Attribute holding reset_type data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(label: str, reset_type: str, **kwargs) -> Any`: Executes __init__ logic.
  - `callback(interaction: discord.Interaction) -> Any`: Executes callback logic.

## Functions

### `_ti(interaction: discord.Interaction, *keys, fallback: str) -> str`
Translate a key using the guild language from an interaction context.

Falls back to ``fallback`` (or the last key segment) when LanguageManager
is unavailable or the key is missing.
