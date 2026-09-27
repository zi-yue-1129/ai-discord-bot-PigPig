# File: `llm/prompting/manager.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `manager` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `PromptManager`
YAML 基礎的系統提示管理器

- **Attributes**:
  - `config_path` (`Any`): Instance attribute for config_path.
  - `loader` (`Any`): Instance attribute for loader.
  - `cache` (`Any`): Instance attribute for cache.
  - `builder` (`Any`): Instance attribute for builder.
  - `file_watcher` (`Any`): Instance attribute for file_watcher.
  - `logger` (`Any`): Instance attribute for logger.
  - `_initialized` (`Any`): Instance attribute for _initialized.

- **Methods**:
  - `__init__(config_path) -> Any`: 初始化提示管理器
  - `_initialize() -> Any`: 初始化管理器
  - `_validate_config(config) -> bool`: 驗證配置的基本結構
  - `get_system_prompt(bot_id, message) -> str`: 取得系統提示（替換原有的 get_system_prompt 函式）
  - `_get_language_key(message) -> str`: 取得語言鍵值用於快取
  - `_apply_dynamic_replacements(prompt, bot_id, message) -> str`: 套用動態替換（整合現有語言管理功能）
  - `_get_fallback_prompt(bot_id) -> str`: 降級策略：使用硬編碼的基本提示
  - `reload_prompts() -> bool`: 重新載入提示配置
  - `_on_config_changed(path) -> Any`: 配置檔案變更回調
  - `get_module_prompt(module_name) -> str`: 取得特定模組的提示內容
  - `compose_prompt(modules) -> str`: 組合指定模組的提示內容
  - `get_available_modules() -> List[...]`: 取得可用的模組列表
  - `validate_modules(modules) -> Dict[...]`: 驗證模組是否存在
  - `get_cache_stats() -> Dict[...]`: 取得快取統計資訊
  - `get_manager_info() -> Dict[...]`: 取得管理器資訊
  - `cleanup() -> Any`: 清理資源

## Functions

### `get_prompt_manager(config_path) -> PromptManager`
取得指定 config_path 的 PromptManager 實例（若不存在則建立並快取）。
