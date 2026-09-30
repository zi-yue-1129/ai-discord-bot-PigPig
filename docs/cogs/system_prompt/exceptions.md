# File: `cogs/system_prompt/exceptions.py`

## Overview
頻道系統提示管理模組的自訂例外類別

定義了所有與系統提示相關的例外狀況，提供明確的錯誤處理機制。

## Classes

### `SystemPromptError`
系統提示相關錯誤的基類

- **Attributes**:
  - `error_code` (`Any`): Instance attribute error_code

- **Methods**:
  - None

### `PermissionError`
權限不足錯誤

- **Attributes**:
  - `required_permission` (`Any`): Instance attribute required_permission

- **Methods**:
  - `_get_localized_message(self, key, lang_manager, guild_id) -> str`: 獲取本地化訊息

### `ValidationError`
驗證失敗錯誤

- **Attributes**:
  - `field` (`Any`): Instance attribute field

- **Methods**:
  - `_get_localized_message(self, key, lang_manager, guild_id, field) -> str`: 獲取本地化訊息

### `ConfigurationError`
配置錯誤

- **Attributes**:
  - `config_path` (`Any`): Instance attribute config_path

- **Methods**:
  - `_get_localized_message(self, key, lang_manager, guild_id) -> str`: 獲取本地化訊息

### `ContentTooLongError`
內容過長錯誤

- **Attributes**:
  - `max_length` (`Any`): Instance attribute max_length
  - `current_length` (`Any`): Instance attribute current_length

- **Methods**:
  - None

### `ChannelNotFoundError`
頻道未找到錯誤

- **Attributes**:
  - `channel_id` (`Any`): Instance attribute channel_id

- **Methods**:
  - None

### `PromptNotFoundError`
系統提示未找到錯誤

- **Attributes**:
  - `scope` (`Any`): Instance attribute scope
  - `target_id` (`Any`): Instance attribute target_id

- **Methods**:
  - None

### `OperationTimeoutError`
操作超時錯誤

- **Attributes**:
  - `operation` (`Any`): Instance attribute operation
  - `timeout_seconds` (`Any`): Instance attribute timeout_seconds

- **Methods**:
  - None

### `ModuleNotFoundError`
模組未找到錯誤

- **Attributes**:
  - `module_name` (`Any`): Instance attribute module_name

- **Methods**:
  - None

### `UnsafeContentError`
不安全內容錯誤

- **Attributes**:
  - `detected_pattern` (`Any`): Instance attribute detected_pattern

- **Methods**:
  - None

## Functions

None
