# File: `cogs/system_prompt/manager.py`

## Overview
Channel system prompt manager.

Provides core system prompt management functionality, including three-level inheritance,
caching system, and configuration management.

## Classes

### `SystemPromptCache`
System prompt cache manager.

- **Attributes**:
  - `cache` (`Dict[Tuple[str, Tuple[Tuple[float, str]]]]`): Attribute holding cache data.
  - `ttl` (`Any`): Attribute holding ttl data.

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
  - `bot` (`Any`): Attribute holding bot data.

- **Methods**:
  - `__init__(bot: discord.Client) -> Any`: Initialize system prompt validator.
  - `validate_prompt_content(content: str) -> Tuple[Tuple[bool, str]]`: Validate prompt content.
  - `validate_modules(modules: Dict[Tuple[str, str]], guild_id: Optional[str]) -> Tuple[Tuple[bool, str]]`: Validate module configuration.

### `SystemPromptManager`
System prompt manager - Core coordinator.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `logger` (`Any`): Attribute holding logger data.
  - `cache` (`Any`): Attribute holding cache data.
  - `validator` (`Any`): Attribute holding validator data.
  - `permission_validator` (`Any`): Attribute holding permission_validator data.
  - `data_dir` (`Any`): Attribute holding data_dir data.
  - `_prompt_manager` (`Any`): Attribute holding _prompt_manager data.

- **Methods**:
  - `__init__(bot: discord.Client) -> Any`: Initialize system prompt manager.
  - `_init_prompt_manager() -> None`: Initialize YAML prompt manager.
  - `get_effective_prompt(channel_id: str, guild_id: str, message: Optional[discord.Message]) -> Dict[Tuple[str, Any]]`: Get effective system prompt (integrated three-level inheritance).
  - `get_channel_prompt_config(guild_id: str, channel_id: str) -> Optional[Dict[Tuple[str, Any]]]`: 取得指定頻道的原始系統提示設定。
  - `set_channel_prompt(guild_id: str, channel_id: str, prompt_data: Dict[Tuple[str, Any]], user_id: str) -> bool`: 設定頻道系統提示
  - `set_server_prompt(guild_id: str, prompt_data: Dict[Tuple[str, Any]], user_id: str) -> bool`: 設定伺服器級別系統提示
  - `remove_channel_prompt(guild_id: str, channel_id: str) -> bool`: 移除頻道系統提示
  - `remove_server_prompt(guild_id: str) -> bool`: 移除伺服器級別系統提示
  - `copy_channel_prompt(source_guild: str, source_channel: str, target_guild: str, target_channel: str) -> bool`: 複製頻道提示設定
  - `get_available_modules() -> List[str]`: 取得可覆蓋的 YAML 模組列表
  - `get_default_module_content(module_name: str) -> str`: 獲取指定模組的預設內容
  - `get_effective_full_prompt(channel_id: str, guild_id: str, for_editing: bool) -> str`: 獲取當前有效的完整系統提示（用於直接編輯時顯示）
  - `get_module_descriptions(lang: str) -> Dict[Tuple[str, str]]`: 獲取模組說明字典
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
  - `_load_guild_config(guild_id: str) -> Dict[Tuple[str, Any]]`: 載入伺服器配置
  - `_save_guild_config(guild_id: str, config: Dict[Tuple[str, Any]]) -> None`: 保存伺服器配置
  - `_get_default_config() -> Dict[Tuple[str, Any]]`: 取得預設配置
  - `_get_yaml_prompt(guild_id: str, message: Optional[discord.Message]) -> Dict[Tuple[str, Any]]`: 取得 YAML 基礎提示
  - `_append_protected_suffix(prompt: str) -> str`: Re-appends critical protected modules (output_format, reminders) from base YAML.
  - `_apply_server_overrides(base_prompt: str, server_config: Dict[Tuple[str, Any]], guild_id: Optional[str]) -> str`: 應用伺服器級別覆蓋
  - `_apply_channel_overrides(base_prompt: str, channel_config: Dict[Tuple[str, Any]], guild_id: Optional[str]) -> str`: 應用頻道級別覆蓋
  - `_apply_language_localization(prompt: str, lang: str, guild_id: str) -> str`: 應用語言本地化
  - `_rebuild_prompt_with_module_overrides(module_overrides: Dict[Tuple[str, str]], override_modules: List[str]) -> str`: 使用模組覆蓋重新建構 YAML 提示
  - `_apply_variable_replacements(prompt: str, guild_id: Optional[str]) -> str`: 對系統提示應用變數替換
  - `_get_system_variables() -> Dict[Tuple[str, Any]]`: 獲取系統變數字典
  - `_get_language(guild_id: str, message: Optional[discord.Message]) -> str`: 取得語言設定
  - `debug_cache_state(guild_id: str, channel_id: str) -> Dict[Tuple[str, Any]]`: 快取狀態除錯（供管理員使用）
  - `get_diagnostics() -> Dict[Tuple[str, Any]]`: 取得診斷資訊
  - `handle_discord_interaction_cache_issues(interaction) -> Dict[Tuple[str, Any]]`: 處理 Discord 互動的快取問題（整合版）
  - `reload_all_configs() -> bool`: 重新載入所有配置（用於 UI 介面）

## Functions

No top-level functions defined.
