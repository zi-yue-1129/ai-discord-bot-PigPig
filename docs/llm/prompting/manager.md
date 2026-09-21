# File: `llm/prompting/manager.py`

## Overview
This file is part of the llm subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `PromptManager`
YAML 基礎的系統提示管理器

- **Attributes**:
  - `config_path` (`Any`): Attribute holding config_path data.
  - `loader` (`Any`): Attribute holding loader data.
  - `cache` (`Any`): Attribute holding cache data.
  - `builder` (`Any`): Attribute holding builder data.
  - `file_watcher` (`Any`): Attribute holding file_watcher data.
  - `logger` (`Any`): Attribute holding logger data.
  - `_initialized` (`Any`): Attribute holding _initialized data.

- **Methods**:
  - `__init__(config_path: str) -> Any`: 初始化提示管理器
  - `_initialize() -> Any`: 初始化管理器
  - `_validate_config(config: dict) -> bool`: 驗證配置的基本結構
  - `get_system_prompt(bot_id: str, message) -> str`: 取得系統提示（替換原有的 get_system_prompt 函式）
  - `_get_language_key(message) -> str`: 取得語言鍵值用於快取
  - `_apply_dynamic_replacements(prompt: str, bot_id: str, message) -> str`: 套用動態替換（整合現有語言管理功能）
  - `_get_fallback_prompt(bot_id: str) -> str`: 降級策略：使用硬編碼的基本提示
  - `reload_prompts() -> bool`: 重新載入提示配置
  - `_on_config_changed(path: str) -> Any`: 配置檔案變更回調
  - `get_module_prompt(module_name: str) -> str`: 取得特定模組的提示內容
  - `compose_prompt(modules: Optional[List[str]]) -> str`: 組合指定模組的提示內容
  - `get_available_modules() -> List[str]`: 取得可用的模組列表
  - `validate_modules(modules: List[str]) -> Dict[Tuple[str, bool]]`: 驗證模組是否存在
  - `get_cache_stats() -> Dict[Tuple[str, Any]]`: 取得快取統計資訊
  - `get_manager_info() -> Dict[Tuple[str, Any]]`: 取得管理器資訊
  - `cleanup() -> Any`: 清理資源

## Functions

### `get_prompt_manager(config_path: str) -> PromptManager`
取得指定 config_path 的 PromptManager 實例（若不存在則建立並快取）。
這樣可以支援多個不同 agent 的配置檔案，而不會互相覆寫單一全域實例。

Args:
    config_path: 配置檔案路徑

Returns:
    PromptManager 實例
