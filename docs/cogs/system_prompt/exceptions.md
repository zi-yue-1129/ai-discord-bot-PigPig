# File: `cogs/system_prompt/exceptions.py`

## Overview
頻道系統提示管理模組的自訂例外類別

定義了所有與系統提示相關的例外狀況，提供明確的錯誤處理機制。

## Classes

### `SystemPromptError`
系統提示相關錯誤的基類

- **Attributes**:
  - `error_code` (`Any`): Attribute holding error_code data.

- **Methods**:
  - `__init__(message: str, error_code: Optional[str]) -> Any`: 初始化系統提示錯誤

### `PermissionError`
權限不足錯誤

- **Attributes**:
  - `required_permission` (`Any`): Attribute holding required_permission data.

- **Methods**:
  - `__init__(message: Optional[str], required_permission: Optional[str], lang_manager, guild_id: Optional[str]) -> Any`: 初始化權限錯誤
  - `_get_localized_message(key: str, lang_manager, guild_id: Optional[str]) -> str`: 獲取本地化訊息

### `ValidationError`
驗證失敗錯誤

- **Attributes**:
  - `field` (`Any`): Attribute holding field data.

- **Methods**:
  - `__init__(message: Optional[str], field: Optional[str], lang_manager, guild_id: Optional[str]) -> Any`: 初始化驗證錯誤
  - `_get_localized_message(key: str, lang_manager, guild_id: Optional[str], field: Optional[str]) -> str`: 獲取本地化訊息

### `ConfigurationError`
配置錯誤

- **Attributes**:
  - `config_path` (`Any`): Attribute holding config_path data.

- **Methods**:
  - `__init__(message: Optional[str], config_path: Optional[str], lang_manager, guild_id: Optional[str]) -> Any`: 初始化配置錯誤
  - `_get_localized_message(key: str, lang_manager, guild_id: Optional[str]) -> str`: 獲取本地化訊息

### `ContentTooLongError`
內容過長錯誤

- **Attributes**:
  - `max_length` (`Any`): Attribute holding max_length data.
  - `current_length` (`Any`): Attribute holding current_length data.

- **Methods**:
  - `__init__(max_length: int, current_length: int, lang_manager, guild_id) -> Any`: 初始化內容過長錯誤

### `ChannelNotFoundError`
頻道未找到錯誤

- **Attributes**:
  - `channel_id` (`Any`): Attribute holding channel_id data.

- **Methods**:
  - `__init__(channel_id: str, lang_manager, guild_id) -> Any`: 初始化頻道未找到錯誤

### `PromptNotFoundError`
系統提示未找到錯誤

- **Attributes**:
  - `scope` (`Any`): Attribute holding scope data.
  - `target_id` (`Any`): Attribute holding target_id data.

- **Methods**:
  - `__init__(scope: str, target_id: str, lang_manager, guild_id) -> Any`: 初始化系統提示未找到錯誤

### `OperationTimeoutError`
操作超時錯誤

- **Attributes**:
  - `operation` (`Any`): Attribute holding operation data.
  - `timeout_seconds` (`Any`): Attribute holding timeout_seconds data.

- **Methods**:
  - `__init__(operation: str, timeout_seconds: float, lang_manager, guild_id) -> Any`: 初始化操作超時錯誤

### `ModuleNotFoundError`
模組未找到錯誤

- **Attributes**:
  - `module_name` (`Any`): Attribute holding module_name data.

- **Methods**:
  - `__init__(module_name: str, lang_manager, guild_id) -> Any`: 初始化模組未找到錯誤

### `UnsafeContentError`
不安全內容錯誤

- **Attributes**:
  - `detected_pattern` (`Any`): Attribute holding detected_pattern data.

- **Methods**:
  - `__init__(detected_pattern: str, lang_manager, guild_id) -> Any`: 初始化不安全內容錯誤

## Functions

No top-level functions defined.
