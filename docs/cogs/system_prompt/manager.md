# File: `cogs/system_prompt/manager.py`

## Overview
This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `manager.py`, providing vital integrations within the PigPig bot ecosystem.
Channel system prompt manager.

Provides core system prompt management functionality, including three-level inheritance,
caching system, and configuration management.

## Classes

### `SystemPromptCache`
System prompt cache manager.

- **Attributes**:
  - `ttl` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(ttl: int) -> Any`: Initialize cache manager.
  - `get_cache_key(guild_id: str, channel_id: str, lang: str) -> str`: Generate cache key.
  - `get(guild_id: str, channel_id: str, lang: str) -> Optional[str]`: Get system prompt from cache.
  - `set(guild_id: str, channel_id: str, prompt: str, lang: str) -> None`: Set cache.
  - `invalidate(guild_id: str, channel_id: Optional[str]) -> None`: Invalidate cache.
  - `clear_all() -> None`: Clear all cache.

### `PromptValidator`
System prompt validator.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: discord.Client) -> Any`: Initialize system prompt validator.
  - `validate_prompt_content(content: str) -> Tuple[Tuple]`: Validate prompt content.
  - `validate_modules(modules: Dict[Tuple], guild_id: Optional[str]) -> Tuple[Tuple]`: Validate module configuration.

### `SystemPromptManager`
System prompt manager - Core coordinator.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.
  - `cache` (`Any`): Internal instance state.
  - `validator` (`Any`): Internal instance state.
  - `permission_validator` (`Any`): Internal instance state.
  - `data_dir` (`Any`): Internal instance state.
  - `_prompt_manager` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: discord.Client) -> Any`: Initialize system prompt manager.
  - `_init_prompt_manager() -> None`: Initialize YAML prompt manager.
  - `get_effective_prompt(channel_id: str, guild_id: str, message: Optional[discord.Message]) -> Dict[Tuple]`: Get effective system prompt (integrated three-level inheritance).
  - `get_channel_prompt_config(guild_id: str, channel_id: str) -> Optional[Dict[Tuple]]`: 取得指定頻道的原始系統提示設定。
  - `set_channel_prompt(guild_id: str, channel_id: str, prompt_data: Dict[Tuple], user_id: str) -> bool`: 設定頻道系統提示
  - `set_server_prompt(guild_id: str, prompt_data: Dict[Tuple], user_id: str) -> bool`: 設定伺服器級別系統提示
  - `remove_channel_prompt(guild_id: str, channel_id: str) -> bool`: 移除頻道系統提示
  - `remove_server_prompt(guild_id: str) -> bool`: 移除伺服器級別系統提示
  - `copy_channel_prompt(source_guild: str, source_channel: str, target_guild: str, target_channel: str) -> bool`: 複製頻道提示設定
  - `get_available_modules() -> List[str]`: 取得可覆蓋的 YAML 模組列表
  - `get_default_module_content(module_name: str) -> str`: 獲取指定模組的預設內容
  - `get_effective_full_prompt(channel_id: str, guild_id: str, for_editing: bool) -> str`: 獲取當前有效的完整系統提示（用於直接編輯時顯示）
  - `get_module_descriptions(lang: str) -> Dict[Tuple]`: 獲取模組說明字典
  - `clear_cache(guild_id: Optional[str], channel_id: Optional[str]) -> None`: 清除快取（全面同步清除）
  - `force_clear_all_caches(guild_id: str, channel_id: Optional[str], interaction: Optional[object]) -> None`: 強制清除所有相關快取（整合版）- 異步版本
  - `_enhanced_force_clear_all_caches(guild_id: str, channel_id: Optional[str]) -> None`: 增強的強制清除所有相關快取方法（整合版）
  - `_legacy_force_clear_all_caches(guild_id: str, channel_id: Optional[str]) -> None`: 原有的強制清除所有相關快取方法（降級使用）
  - `reload_system_prompts(guild_id: str, channel_id: Optional[str]) -> bool`: 重新載入系統提示配置（完整重新載入方案）
  - `_clear_yaml_prompt_cache(guild_id: Optional[str], channel_id: Optional[str]) -> None`: 清除 YAML PromptManager 的相關快取
  - `_force_clear_yaml_cache(guild_id: str) -> None`: 強制清除 YAML PromptManager 的所有相關快取
  - `_force_clear_sendmessage_cache(guild_id: str, channel_id: Optional[str]) -> None`: 強制清除 prompting 模組的所有相關快取
  - `_clear_hidden_caches(guild_id: str, channel_id: Optional[str]) -> None`: 清除可能的隱藏快取層級
  - `_deep_cache_cleanup(guild_id: str, channel_id: Optional[str]) -> None`: 深度快取清理（額外的清除策略）
  - `_reinitialize_components() -> None`: 重新初始化相關組件
  - `_verify_reload_result(guild_id: str, channel_id: Optional[str]) -> bool`: 驗證重新載入結果
  - `_load_guild_config(guild_id: str) -> Dict[Tuple]`: 載入伺服器配置
  - `_save_guild_config(guild_id: str, config: Dict[Tuple]) -> None`: 保存伺服器配置
  - `_get_default_config() -> Dict[Tuple]`: 取得預設配置
  - `_get_yaml_prompt(guild_id: str, message: Optional[discord.Message]) -> Dict[Tuple]`: 取得 YAML 基礎提示
  - `_append_protected_suffix(prompt: str) -> str`: Re-appends critical protected modules (output_format, reminders) from base YAML.
  - `_apply_server_overrides(base_prompt: str, server_config: Dict[Tuple], guild_id: Optional[str]) -> str`: 應用伺服器級別覆蓋
  - `_apply_channel_overrides(base_prompt: str, channel_config: Dict[Tuple], guild_id: Optional[str]) -> str`: 應用頻道級別覆蓋
  - `_apply_language_localization(prompt: str, lang: str, guild_id: str) -> str`: 應用語言本地化
  - `_rebuild_prompt_with_module_overrides(module_overrides: Dict[Tuple], override_modules: List[str]) -> str`: 使用模組覆蓋重新建構 YAML 提示
  - `_apply_variable_replacements(prompt: str, guild_id: Optional[str]) -> str`: 對系統提示應用變數替換
  - `_get_system_variables() -> Dict[Tuple]`: 獲取系統變數字典
  - `_get_language(guild_id: str, message: Optional[discord.Message]) -> str`: 取得語言設定
  - `debug_cache_state(guild_id: str, channel_id: str) -> Dict[Tuple]`: 快取狀態除錯（供管理員使用）
  - `get_diagnostics() -> Dict[Tuple]`: 取得診斷資訊
  - `handle_discord_interaction_cache_issues(interaction: Any) -> Dict[Tuple]`: 處理 Discord 互動的快取問題（整合版）
  - `reload_all_configs() -> bool`: 重新載入所有配置（用於 UI 介面）


## Handwritten Context
# System Prompt System - Manager

**File:** [`cogs/system_prompt/manager.py`](cogs/system_prompt/manager.py)

The `SystemPromptManager` is the core engine of the system prompt feature. It handles the complex logic of inheriting and combining prompts from different levels, manages caching, and ensures content is safe.

## `SystemPromptManager` Class

### `__init__(self, bot)`

Initializes the manager, creating instances of the `SystemPromptCache`, `PromptValidator`, and `PermissionValidator`. It also sets up the data directory for storing configuration files.

### `get_effective_prompt(self, channel_id, guild_id, ...)`

This is the most important method in the manager. It calculates the final system prompt to be used for a given channel by applying the three-tiered inheritance model.

*   **Process:**
    1.  **Cache Check:** It first checks the `SystemPromptCache` for a valid, non-expired entry for the channel. If found, it returns the cached prompt immediately.
    2.  **Tier 1 (Base):** It retrieves the base prompt from the YAML files using the `gpt.prompting.manager`.
    3.  **Tier 2 (Server):** It loads the server's configuration file (`{guild_id}.json`) and applies the `server_level` overrides to the base prompt using `_apply_server_overrides`.
    4.  **Tier 3 (Channel):** It then applies the channel-specific overrides from the configuration file using `_apply_channel_overrides`.
    5.  **Localization & Variables:** It applies language localizations and replaces dynamic variables (like `{current_time}`).
    6.  **Cache Update:** The final, combined prompt is stored in the cache for future use.
*   **Returns:** A dictionary containing the final `prompt` string and its `source` (e.g., 'cache', 'channel', 'server', 'yaml').

### Configuration Management

*   **`set_channel_prompt(...)` / `set_server_prompt(...)`:** These methods handle the saving of new or updated prompt configurations. They first validate the input using the `PromptValidator` and then write the data to the appropriate JSON configuration file.
*   **`remove_channel_prompt(...)` / `remove_server_prompt(...)`:** These methods remove the configuration for a channel or a server, causing them to fall back to the next level of the inheritance chain.
*   **`_load_guild_config(...)` / `_save_guild_config(...)`:** Private methods for reading from and writing to the per-server JSON files.

### Caching (`SystemPromptCache`)

The manager uses an in-memory `SystemPromptCache` with a Time-To-Live (TTL).
*   **`get(...)`:** Retrieves a prompt from the cache if it's not expired.
*   **`set(...)`:** Stores a newly generated prompt in the cache with a timestamp.
*   **`invalidate(...)`:** Clears the cache for a specific channel or an entire server. This is called automatically whenever a prompt is updated or removed to ensure changes take effect immediately.

### Validation (`PromptValidator`)

This internal class ensures the safety and integrity of user-provided prompts.
*   **`validate_prompt_content(...)`:** Checks if the prompt content exceeds the maximum length (`MAX_PROMPT_LENGTH`) and scans it for potentially malicious code patterns (like `<script>` tags or `javascript:` URIs) using a list of regular expressions.