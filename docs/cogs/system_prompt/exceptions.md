# File: `cogs/system_prompt/exceptions.py`

## Overview
頻道系統提示管理模組的自訂例外類別

## Classes

### `SystemPromptError`
系統提示相關錯誤的基類

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(message: str, error_code: Optional[str]) -> Any`: 初始化系統提示錯誤

### `PermissionError`
權限不足錯誤

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(message: Optional[str], required_permission: Optional[str], lang_manager, guild_id: Optional[str]) -> Any`: 初始化權限錯誤
  - `_get_localized_message(key: str, lang_manager, guild_id: Optional[str]) -> str`: 獲取本地化訊息

### `ValidationError`
驗證失敗錯誤

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(message: Optional[str], field: Optional[str], lang_manager, guild_id: Optional[str]) -> Any`: 初始化驗證錯誤
  - `_get_localized_message(key: str, lang_manager, guild_id: Optional[str], field: Optional[str]) -> str`: 獲取本地化訊息

### `ConfigurationError`
配置錯誤

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(message: Optional[str], config_path: Optional[str], lang_manager, guild_id: Optional[str]) -> Any`: 初始化配置錯誤
  - `_get_localized_message(key: str, lang_manager, guild_id: Optional[str]) -> str`: 獲取本地化訊息

### `ContentTooLongError`
內容過長錯誤

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(max_length: int, current_length: int, lang_manager, guild_id) -> Any`: 初始化內容過長錯誤

### `ChannelNotFoundError`
頻道未找到錯誤

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(channel_id: str, lang_manager, guild_id) -> Any`: 初始化頻道未找到錯誤

### `PromptNotFoundError`
系統提示未找到錯誤

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(scope: str, target_id: str, lang_manager, guild_id) -> Any`: 初始化系統提示未找到錯誤

### `OperationTimeoutError`
操作超時錯誤

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(operation: str, timeout_seconds: float, lang_manager, guild_id) -> Any`: 初始化操作超時錯誤

### `ModuleNotFoundError`
模組未找到錯誤

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(module_name: str, lang_manager, guild_id) -> Any`: 初始化模組未找到錯誤

### `UnsafeContentError`
不安全內容錯誤

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(detected_pattern: str, lang_manager, guild_id) -> Any`: 初始化不安全內容錯誤

## Functions

No module-level functions defined in this file.
