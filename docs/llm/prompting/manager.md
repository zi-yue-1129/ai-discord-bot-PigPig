# File: `llm/prompting/manager.py`

## Overview
The `PromptManager` class provides a comprehensive YAML-based prompt management system that coordinates configuration loading, caching, building, and file monitoring. It serves as the central orchestrator for the prompting subsystem.

## Classes

### `PromptManager`
YAML 基礎的系統提示管理器

- **Attributes**:
  - `config_path` (`Any`): Instance attribute managing config_path.
  - `loader` (`Any`): Instance attribute managing loader.
  - `cache` (`Any`): Instance attribute managing cache.
  - `builder` (`Any`): Instance attribute managing builder.
  - `file_watcher` (`Any`): Instance attribute managing file_watcher.
  - `logger` (`Any`): Instance attribute managing logger.
  - `_initialized` (`Any`): Instance attribute managing _initialized.

- **Methods**:
  - `get_system_prompt(bot_id, message) -> str`: 取得系統提示（替換原有的 get_system_prompt 函式）  Args:     bot_id: Discord 機器人 ID     message: Discord 訊息物件（用於語言檢測）      Returns:     完整的系統提示字串
  - `reload_prompts() -> bool`: 重新載入提示配置  Returns:     bool: 是否成功重新載入
  - `get_module_prompt(module_name) -> str`: 取得特定模組的提示內容  Args:     module_name: 模組名稱      Returns:     模組提示內容
  - `compose_prompt(modules) -> str`: 組合指定模組的提示內容  Args:     modules: 要組合的模組列表，如果為 None 則使用預設模組  Returns:     組合後的提示內容
  - `get_available_modules() -> List[str]`: 取得可用的模組列表  Returns:     可用模組名稱列表
  - `validate_modules(modules) -> Dict[Tuple[str, bool]]`: 驗證模組是否存在  Args:     modules: 要驗證的模組列表      Returns:     模組驗證結果字典 {模組名: 是否存在}
  - `get_cache_stats() -> Dict[Tuple[str, Any]]`: 取得快取統計資訊  Returns:     快取統計資訊字典
  - `get_manager_info() -> Dict[Tuple[str, Any]]`: 取得管理器資訊  Returns:     管理器資訊字典
  - `cleanup() -> Any`: 清理資源

## Functions

### `get_prompt_manager(config_path) -> PromptManager`
取得指定 config_path 的 PromptManager 實例（若不存在則建立並快取）。
這樣可以支援多個不同 agent 的配置檔案，而不會互相覆寫單一全域實例。

Args:
    config_path: 配置檔案路徑

Returns:
    PromptManager 實例

