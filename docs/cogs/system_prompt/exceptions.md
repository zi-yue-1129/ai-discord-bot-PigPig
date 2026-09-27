# File: `cogs/system_prompt/exceptions.py`

## Overview
頻道系統提示管理模組的自訂例外類別

定義了所有與系統提示相關的例外狀況，提供明確的錯誤處理機制。

## Classes

### `SystemPromptError`
系統提示相關錯誤的基類

- **Attributes**:
  - `error_code` (`Any`): Instance attribute for error_code.

- **Methods**:
  - `__init__(message, error_code) -> Any`: 初始化系統提示錯誤

### `PermissionError`
權限不足錯誤

- **Attributes**:
  - `required_permission` (`Any`): Instance attribute for required_permission.

- **Methods**:
  - `__init__(message, required_permission, lang_manager, guild_id) -> Any`: 初始化權限錯誤
  - `_get_localized_message(key, lang_manager, guild_id) -> str`: 獲取本地化訊息

### `ValidationError`
驗證失敗錯誤

- **Attributes**:
  - `field` (`Any`): Instance attribute for field.

- **Methods**:
  - `__init__(message, field, lang_manager, guild_id) -> Any`: 初始化驗證錯誤
  - `_get_localized_message(key, lang_manager, guild_id, field) -> str`: 獲取本地化訊息

### `ConfigurationError`
配置錯誤

- **Attributes**:
  - `config_path` (`Any`): Instance attribute for config_path.

- **Methods**:
  - `__init__(message, config_path, lang_manager, guild_id) -> Any`: 初始化配置錯誤
  - `_get_localized_message(key, lang_manager, guild_id) -> str`: 獲取本地化訊息

### `ContentTooLongError`
內容過長錯誤

- **Attributes**:
  - `max_length` (`Any`): Instance attribute for max_length.
  - `current_length` (`Any`): Instance attribute for current_length.

- **Methods**:
  - `__init__(max_length, current_length, lang_manager, guild_id) -> Any`: 初始化內容過長錯誤

### `ChannelNotFoundError`
頻道未找到錯誤

- **Attributes**:
  - `channel_id` (`Any`): Instance attribute for channel_id.

- **Methods**:
  - `__init__(channel_id, lang_manager, guild_id) -> Any`: 初始化頻道未找到錯誤

### `PromptNotFoundError`
系統提示未找到錯誤

- **Attributes**:
  - `scope` (`Any`): Instance attribute for scope.
  - `target_id` (`Any`): Instance attribute for target_id.

- **Methods**:
  - `__init__(scope, target_id, lang_manager, guild_id) -> Any`: 初始化系統提示未找到錯誤

### `OperationTimeoutError`
操作超時錯誤

- **Attributes**:
  - `operation` (`Any`): Instance attribute for operation.
  - `timeout_seconds` (`Any`): Instance attribute for timeout_seconds.

- **Methods**:
  - `__init__(operation, timeout_seconds, lang_manager, guild_id) -> Any`: 初始化操作超時錯誤

### `ModuleNotFoundError`
模組未找到錯誤

- **Attributes**:
  - `module_name` (`Any`): Instance attribute for module_name.

- **Methods**:
  - `__init__(module_name, lang_manager, guild_id) -> Any`: 初始化模組未找到錯誤

### `UnsafeContentError`
不安全內容錯誤

- **Attributes**:
  - `detected_pattern` (`Any`): Instance attribute for detected_pattern.

- **Methods**:
  - `__init__(detected_pattern, lang_manager, guild_id) -> Any`: 初始化不安全內容錯誤
