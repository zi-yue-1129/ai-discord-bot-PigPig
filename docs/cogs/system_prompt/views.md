# File: `cogs/system_prompt/views.py`

## Overview
系統提示管理的統一 UI 選單系統

## Classes

### `LocalizedView`
Base class for all system-prompt views.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(manager: str, guild_id: str, timeout: float) -> Any`: No description provided.
  - `_t(*keys: str, fallback: str) -> str`: Translate *keys* using the guild's language.

### `SystemPromptMainView`
系統提示管理主選單

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, guild_id: str, timeout: float) -> Any`: No description provided.
  - `_setup_main_buttons() -> Any`: 設定主要功能按鈕
  - `function_callback(interaction: discord.Interaction, function: str) -> Any`: 處理功能按鈕回調
  - `_handle_set_function(interaction: discord.Interaction) -> Any`: No description provided.
  - `_handle_view_function(interaction: discord.Interaction) -> Any`: No description provided.
  - `_handle_copy_function(interaction: discord.Interaction) -> Any`: No description provided.
  - `_handle_remove_function(interaction: discord.Interaction) -> Any`: No description provided.
  - `_handle_reset_function(interaction: discord.Interaction) -> Any`: No description provided.
  - `_handle_reload_function(interaction: discord.Interaction) -> Any`: No description provided.

### `SystemPromptFunctionButton`
系統提示功能按鈕

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(function: str, **kwargs) -> Any`: No description provided.
  - `callback(interaction: discord.Interaction) -> Any`: 按鈕回調

### `SystemPromptSetView`
設定系統提示的子選單

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, guild_id: str, timeout: float) -> Any`: No description provided.
  - `scope_callback(interaction: discord.Interaction, scope: str) -> Any`: No description provided.

### `EditModeSelectionView`
編輯模式選擇選單

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, scope: str, target_channel: Optional[discord.TextChannel], scope_text: str, guild: discord.Guild, guild_id: str, timeout: float) -> Any`: No description provided.
  - `edit_mode_callback(interaction: discord.Interaction, edit_mode: str) -> Any`: 處理編輯模式選擇
  - `_handle_direct_edit(interaction: discord.Interaction) -> Any`: 處理直接編輯提示
  - `_restore_variable_placeholders(prompt: str, guild_id: str) -> str`: 將已替換的變數還原為占位符格式，以便編輯時顯示原始模板
  - `_handle_module_edit(interaction: discord.Interaction) -> Any`: 處理模組化編輯
  - `_handle_direct_set_callback(interaction: discord.Interaction, content: str) -> Any`: 處理直接設定回調

### `EditModeButton`
編輯模式按鈕

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(edit_mode: str, **kwargs) -> Any`: No description provided.
  - `callback(interaction: discord.Interaction) -> Any`: No description provided.

### `SystemPromptScopeButton`
範圍選擇按鈕

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(scope: str, **kwargs) -> Any`: No description provided.
  - `callback(interaction: discord.Interaction) -> Any`: No description provided.

### `SystemPromptViewOptionsView`
查看配置選項選單

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, guild_id: str, timeout: float) -> Any`: No description provided.
  - `view_callback(interaction: discord.Interaction, view_type: str) -> Any`: 處理查看回調

### `SystemPromptViewButton`
查看選項按鈕

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(view_type: str, **kwargs) -> Any`: No description provided.
  - `callback(interaction: discord.Interaction) -> Any`: No description provided.

### `ModuleEditView`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, modules: List[str], guild: discord.Guild, scope: Optional[str], target_channel: Optional[discord.TextChannel], scope_text: Optional[str], guild_id: str, timeout: float) -> Any`: No description provided.
  - `_setup_scope_selector() -> Any`: No description provided.
  - `_setup_module_selector() -> Any`: No description provided.
  - `scope_callback(interaction: discord.Interaction, scope: str) -> Any`: No description provided.

### `ModuleScopeButton`
模組範圍選擇按鈕

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(scope: str, **kwargs) -> Any`: No description provided.
  - `callback(interaction: discord.Interaction) -> Any`: No description provided.

### `ModuleSelect`
模組選擇器

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(manager: SystemPromptManager, scope: str, channel: Optional[discord.TextChannel], guild: discord.Guild, scope_text: Optional[str], **kwargs) -> Any`: No description provided.
  - `_update_option_descriptions() -> Any`: 更新選項的說明文字 (基於語言管理器)
  - `callback(interaction: discord.Interaction) -> Any`: 選擇器回調
  - `_handle_module_callback(interaction: discord.Interaction, module_name: str, content: str) -> Any`: 處理模組編輯回調

### `SystemPromptCopyView`
複製系統提示選單

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, guild: discord.Guild, guild_id: str, timeout: float) -> Any`: No description provided.

### `SystemPromptRemoveView`
移除系統提示的子選單

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, guild_id: str, timeout: float) -> Any`: No description provided.

### `SystemPromptResetView`
重置系統提示的子選單

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(manager: SystemPromptManager, permission_validator: PermissionValidator, guild_id: str, timeout: float) -> Any`: No description provided.

### `BackButton`
返回主選單按鈕

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(row: int, guild_id: str, bot) -> Any`: No description provided.
  - `callback(interaction: discord.Interaction) -> Any`: 返回主選單

### `ChannelSelect`
頻道選擇器（用於複製功能）

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(**kwargs) -> Any`: No description provided.
  - `callback(interaction: discord.Interaction) -> Any`: No description provided.

### `CopyExecuteButton`
執行複製按鈕

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(label: str, **kwargs) -> Any`: No description provided.
  - `callback(interaction: discord.Interaction) -> Any`: No description provided.

### `RemoveButton`
移除按鈕

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(label: str, remove_type: str, **kwargs) -> Any`: No description provided.
  - `callback(interaction: discord.Interaction) -> Any`: No description provided.

### `ResetButton`
重置按鈕

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(label: str, reset_type: str, **kwargs) -> Any`: No description provided.
  - `callback(interaction: discord.Interaction) -> Any`: No description provided.

## Functions

### `_ti(interaction: discord.Interaction, *keys: str, fallback: str) -> str`
Translate a key using the guild language from an interaction context.
