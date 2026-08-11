# File: `cogs/system_prompt/exceptions.py`

## Overview
頻道系統提示管理模組的自訂例外類別

定義了所有與系統提示相關的例外狀況，提供明確的錯誤處理機制。

## Classes

### `SystemPromptError`
系統提示相關錯誤的基類

- **Attributes**:
  - `error_code` (`Any`): Instance attribute managing error_code.

### `PermissionError`
權限不足錯誤

- **Attributes**:
  - `required_permission` (`Any`): Instance attribute managing required_permission.

### `ValidationError`
驗證失敗錯誤

- **Attributes**:
  - `field` (`Any`): Instance attribute managing field.

### `ConfigurationError`
配置錯誤

- **Attributes**:
  - `config_path` (`Any`): Instance attribute managing config_path.

### `ContentTooLongError`
內容過長錯誤

- **Attributes**:
  - `max_length` (`Any`): Instance attribute managing max_length.
  - `current_length` (`Any`): Instance attribute managing current_length.

### `ChannelNotFoundError`
頻道未找到錯誤

- **Attributes**:
  - `channel_id` (`Any`): Instance attribute managing channel_id.

### `PromptNotFoundError`
系統提示未找到錯誤

- **Attributes**:
  - `scope` (`Any`): Instance attribute managing scope.
  - `target_id` (`Any`): Instance attribute managing target_id.

### `OperationTimeoutError`
操作超時錯誤

- **Attributes**:
  - `operation` (`Any`): Instance attribute managing operation.
  - `timeout_seconds` (`Any`): Instance attribute managing timeout_seconds.

### `ModuleNotFoundError`
模組未找到錯誤

- **Attributes**:
  - `module_name` (`Any`): Instance attribute managing module_name.

### `UnsafeContentError`
不安全內容錯誤

- **Attributes**:
  - `detected_pattern` (`Any`): Instance attribute managing detected_pattern.

