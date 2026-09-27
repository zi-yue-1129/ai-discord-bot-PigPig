# File: `cogs/system_prompt/manager.py`

## Overview
Channel system prompt manager.

Provides core system prompt management functionality, including three-level inheritance,
caching system, and configuration management.

## Classes

### `SystemPromptCache`
System prompt cache manager.

- **Attributes**:
  - `cache` (`Dict[...]`): Instance attribute for cache.
  - `ttl` (`Any`): Instance attribute for ttl.

- **Methods**:
  - `__init__(ttl) -> Any`: Initialize cache manager.
  - `get_cache_key(guild_id, channel_id, lang) -> str`: Generate cache key.
  - `get(guild_id, channel_id, lang) -> Optional[...]`: Get system prompt from cache.
  - `set(guild_id, channel_id, prompt, lang) -> None`: Set cache.
  - `invalidate(guild_id, channel_id) -> None`: Invalidate cache.
  - `clear_all() -> None`: Clear all cache.

### `PromptValidator`
System prompt validator.

- **Attributes**:
  - `MAX_PROMPT_LENGTH` (`Any`): Class attribute representing MAX_PROMPT_LENGTH.
  - `MAX_MODULE_COUNT` (`Any`): Class attribute representing MAX_MODULE_COUNT.
  - `DANGEROUS_PATTERNS` (`Any`): Class attribute representing DANGEROUS_PATTERNS.
  - `bot` (`Any`): Instance attribute for bot.

- **Methods**:
  - `__init__(bot) -> Any`: Initialize system prompt validator.
  - `validate_prompt_content(content) -> Tuple[...]`: Validate prompt content.
  - `validate_modules(modules, guild_id) -> Tuple[...]`: Validate module configuration.

### `SystemPromptManager`
System prompt manager - Core coordinator.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `logger` (`Any`): Instance attribute for logger.
  - `cache` (`Any`): Instance attribute for cache.
  - `validator` (`Any`): Instance attribute for validator.
  - `permission_validator` (`Any`): Instance attribute for permission_validator.
  - `data_dir` (`Any`): Instance attribute for data_dir.
  - `_prompt_manager` (`Any`): Instance attribute for _prompt_manager.

- **Methods**:
  - `__init__(bot) -> Any`: Initialize system prompt manager.
  - `_init_prompt_manager() -> None`: Initialize YAML prompt manager.
  - `get_effective_prompt(channel_id, guild_id, message) -> Dict[...]`: Get effective system prompt (integrated three-level inheritance).
  - `get_channel_prompt_config(guild_id, channel_id) -> Optional[...]`: 取得指定頻道的原始系統提示設定。
  - `set_channel_prompt(guild_id, channel_id, prompt_data, user_id) -> bool`: 設定頻道系統提示
  - `set_server_prompt(guild_id, prompt_data, user_id) -> bool`: 設定伺服器級別系統提示
  - `remove_channel_prompt(guild_id, channel_id) -> bool`: 移除頻道系統提示
  - `remove_server_prompt(guild_id) -> bool`: 移除伺服器級別系統提示
  - `copy_channel_prompt(source_guild, source_channel, target_guild, target_channel) -> bool`: 複製頻道提示設定
  - `get_available_modules() -> List[...]`: 取得可覆蓋的 YAML 模組列表
  - `get_default_module_content(module_name) -> str`: 獲取指定模組的預設內容
  - `get_effective_full_prompt(channel_id, guild_id, for_editing) -> str`: 獲取當前有效的完整系統提示（用於直接編輯時顯示）
  - `get_module_descriptions(lang) -> Dict[...]`: 獲取模組說明字典
  - `clear_cache(guild_id, channel_id) -> None`: 清除快取（全面同步清除）
  - `force_clear_all_caches(guild_id, channel_id, interaction) -> None`: 強制清除所有相關快取（整合版）- 異步版本
  - `_enhanced_force_clear_all_caches(guild_id, channel_id) -> None`: 增強的強制清除所有相關快取方法（整合版）
  - `_legacy_force_clear_all_caches(guild_id, channel_id) -> None`: 原有的強制清除所有相關快取方法（降級使用）
  - `reload_system_prompts(guild_id, channel_id) -> bool`: 重新載入系統提示配置（完整重新載入方案）
  - `_clear_yaml_prompt_cache(guild_id, channel_id) -> None`: 清除 YAML PromptManager 的相關快取
  - `_force_clear_yaml_cache(guild_id) -> None`: 強制清除 YAML PromptManager 的所有相關快取
  - `_force_clear_sendmessage_cache(guild_id, channel_id) -> None`: 強制清除 prompting 模組的所有相關快取
  - `_clear_hidden_caches(guild_id, channel_id) -> None`: 清除可能的隱藏快取層級
  - `_deep_cache_cleanup(guild_id, channel_id) -> None`: 深度快取清理（額外的清除策略）
  - `_reinitialize_components() -> None`: 重新初始化相關組件
  - `_verify_reload_result(guild_id, channel_id) -> bool`: 驗證重新載入結果
  - `_load_guild_config(guild_id) -> Dict[...]`: 載入伺服器配置
  - `_save_guild_config(guild_id, config) -> None`: 保存伺服器配置
  - `_get_default_config() -> Dict[...]`: 取得預設配置
  - `_get_yaml_prompt(guild_id, message) -> Dict[...]`: 取得 YAML 基礎提示
  - `_append_protected_suffix(prompt) -> str`: Re-appends critical protected modules (output_format, reminders) from base YAML.
  - `_apply_server_overrides(base_prompt, server_config, guild_id) -> str`: 應用伺服器級別覆蓋
  - `_apply_channel_overrides(base_prompt, channel_config, guild_id) -> str`: 應用頻道級別覆蓋
  - `_apply_language_localization(prompt, lang, guild_id) -> str`: 應用語言本地化
  - `_rebuild_prompt_with_module_overrides(module_overrides, override_modules) -> str`: 使用模組覆蓋重新建構 YAML 提示
  - `_apply_variable_replacements(prompt, guild_id) -> str`: 對系統提示應用變數替換
  - `_get_system_variables() -> Dict[...]`: 獲取系統變數字典
  - `_get_language(guild_id, message) -> str`: 取得語言設定
  - `debug_cache_state(guild_id, channel_id) -> Dict[...]`: 快取狀態除錯（供管理員使用）
  - `get_diagnostics() -> Dict[...]`: 取得診斷資訊
  - `handle_discord_interaction_cache_issues(interaction) -> Dict[...]`: 處理 Discord 互動的快取問題（整合版）
  - `reload_all_configs() -> bool`: 重新載入所有配置（用於 UI 介面）
