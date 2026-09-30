# File: `cogs/system_prompt/manager.py`

## Overview
Channel system prompt manager.

Provides core system prompt management functionality, including three-level inheritance,
caching system, and configuration management.

## Classes

### `SystemPromptCache`
System prompt cache manager.

- **Attributes**:
  - `cache` (`Dict[str, Tuple[float, str]]`): Instance attribute cache
  - `ttl` (`Any`): Instance attribute ttl

- **Methods**:
  - `get_cache_key(self, guild_id, channel_id, lang) -> str`: Generate cache key.
  - `get(self, guild_id, channel_id, lang) -> Optional[str]`: Get system prompt from cache.
  - `set(self, guild_id, channel_id, prompt, lang) -> None`: Set cache.
  - `invalidate(self, guild_id, channel_id) -> None`: Invalidate cache.
  - `clear_all(self) -> None`: Clear all cache.

### `PromptValidator`
System prompt validator.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `MAX_PROMPT_LENGTH` (`Any`): Attribute MAX_PROMPT_LENGTH
  - `MAX_MODULE_COUNT` (`Any`): Attribute MAX_MODULE_COUNT
  - `DANGEROUS_PATTERNS` (`Any`): Attribute DANGEROUS_PATTERNS

- **Methods**:
  - `validate_prompt_content(self, content) -> Tuple[bool, str]`: Validate prompt content.  Args:     content: Prompt content.      Returns:     (is_valid, error_message)
  - `validate_modules(self, modules, guild_id) -> Tuple[bool, str]`: Validate module configuration.  Args:     modules: Module dictionary.     guild_id: Server ID (optional).      Returns:     (is_valid, error_message)

### `SystemPromptManager`
System prompt manager - Core coordinator.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `logger` (`Any`): Instance attribute logger
  - `cache` (`Any`): Instance attribute cache
  - `validator` (`Any`): Instance attribute validator
  - `permission_validator` (`Any`): Instance attribute permission_validator
  - `data_dir` (`Any`): Instance attribute data_dir
  - `_prompt_manager` (`Any`): Instance attribute _prompt_manager

- **Methods**:
  - `_init_prompt_manager(self) -> None`: Initialize YAML prompt manager.
  - `get_effective_prompt(self, channel_id, guild_id, message) -> Dict[str, Any]`: Get effective system prompt (integrated three-level inheritance).  Args:     channel_id: Channel ID.     guild_id: Server ID.     message: Discord message object (for language detection).      Returns:     Dictionary containing prompt content and source.
  - `get_channel_prompt_config(self, guild_id, channel_id) -> Optional[Dict[str, Any]]`: 取得指定頻道的原始系統提示設定。  這個方法會直接從設定檔中讀取並回傳該頻道的設定字典， 而不會進行繼承合併或變數替換。  Args:     guild_id: 伺服器 ID。     channel_id: 頻道 ID。  Returns:     包含頻道設定的字典，如果不存在則回傳 None。
  - `set_channel_prompt(self, guild_id, channel_id, prompt_data, user_id) -> bool`: 設定頻道系統提示  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID     prompt_data: 提示資料     user_id: 操作用戶 ID      Returns:     是否設定成功
  - `set_server_prompt(self, guild_id, prompt_data, user_id) -> bool`: 設定伺服器級別系統提示  Args:     guild_id: 伺服器 ID     prompt_data: 提示資料     user_id: 操作用戶 ID      Returns:     是否設定成功
  - `remove_channel_prompt(self, guild_id, channel_id) -> bool`: 移除頻道系統提示  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID      Returns:     是否移除成功
  - `remove_server_prompt(self, guild_id) -> bool`: 移除伺服器級別系統提示  Args:     guild_id: 伺服器 ID      Returns:     是否移除成功
  - `copy_channel_prompt(self, source_guild, source_channel, target_guild, target_channel) -> bool`: 複製頻道提示設定  Args:     source_guild: 來源伺服器 ID     source_channel: 來源頻道 ID     target_guild: 目標伺服器 ID     target_channel: 目標頻道 ID      Returns:     是否複製成功
  - `get_available_modules(self) -> List[str]`: 取得可覆蓋的 YAML 模組列表
  - `get_default_module_content(self, module_name) -> str`: 獲取指定模組的預設內容  Args:     module_name: 模組名稱      Returns:     模組的預設內容字串
  - `get_effective_full_prompt(self, channel_id, guild_id, for_editing) -> str`: 獲取當前有效的完整系統提示（用於直接編輯時顯示）  Args:     channel_id: 頻道 ID     guild_id: 伺服器 ID     for_editing: 是否用於編輯（如果是，返回未替換變數的版本）      Returns:     完整的有效系統提示內容
  - `get_module_descriptions(self, lang) -> Dict[str, str]`: 獲取模組說明字典  Args:     lang: 語言代碼      Returns:     模組名稱對應說明的字典
  - `clear_cache(self, guild_id, channel_id) -> None`: 清除快取（全面同步清除）  Args:     guild_id: 伺服器 ID（可選）     channel_id: 頻道 ID（可選）
  - `force_clear_all_caches(self, guild_id, channel_id, interaction) -> None`: 強制清除所有相關快取（整合版）- 異步版本  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID（可選）     interaction: Discord 互動物件（可選）
  - `_enhanced_force_clear_all_caches(self, guild_id, channel_id) -> None`: 增強的強制清除所有相關快取方法（整合版）  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID（可選）
  - `_legacy_force_clear_all_caches(self, guild_id, channel_id) -> None`: 原有的強制清除所有相關快取方法（降級使用）  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID（可選）
  - `reload_system_prompts(self, guild_id, channel_id) -> bool`: 重新載入系統提示配置（完整重新載入方案）  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID（可選）      Returns:     是否重新載入成功
  - `_clear_yaml_prompt_cache(self, guild_id, channel_id) -> None`: 清除 YAML PromptManager 的相關快取  Args:     guild_id: 伺服器 ID（可選）     channel_id: 頻道 ID（可選）
  - `_force_clear_yaml_cache(self, guild_id) -> None`: 強制清除 YAML PromptManager 的所有相關快取  Args:     guild_id: 伺服器 ID
  - `_force_clear_sendmessage_cache(self, guild_id, channel_id) -> None`: 強制清除 prompting 模組的所有相關快取  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID（可選）
  - `_clear_hidden_caches(self, guild_id, channel_id) -> None`: 清除可能的隱藏快取層級  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID（可選）
  - `_deep_cache_cleanup(self, guild_id, channel_id) -> None`: 深度快取清理（額外的清除策略）  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID（可選）
  - `_reinitialize_components(self) -> None`: 重新初始化相關組件
  - `_verify_reload_result(self, guild_id, channel_id) -> bool`: 驗證重新載入結果  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID（可選）      Returns:     驗證是否成功
  - `_load_guild_config(self, guild_id) -> Dict[str, Any]`: 載入伺服器配置
  - `_save_guild_config(self, guild_id, config) -> None`: 保存伺服器配置
  - `_get_default_config(self) -> Dict[str, Any]`: 取得預設配置
  - `_get_yaml_prompt(self, guild_id, message) -> Dict[str, Any]`: 取得 YAML 基礎提示
  - `_append_protected_suffix(self, prompt) -> str`: Re-appends critical protected modules (output_format, reminders) from base YAML.  Called only after a full `prompt` replacement, which discards the base content. Ensures <som>/<eom> rules and thinking-model ordering are never silently lost. The protected content goes through variable replacement in the caller.
  - `_apply_server_overrides(self, base_prompt, server_config, guild_id) -> str`: 應用伺服器級別覆蓋
  - `_apply_channel_overrides(self, base_prompt, channel_config, guild_id) -> str`: 應用頻道級別覆蓋
  - `_apply_language_localization(self, prompt, lang, guild_id) -> str`: 應用語言本地化
  - `_rebuild_prompt_with_module_overrides(self, module_overrides, override_modules) -> str`: 使用模組覆蓋重新建構 YAML 提示  Args:     module_overrides: 模組覆蓋字典 {模組名: 覆蓋內容}     override_modules: 要覆蓋的模組列表      Returns:     重新建構的提示字串
  - `_apply_variable_replacements(self, prompt, guild_id) -> str`: 對系統提示應用變數替換  Args:     prompt: 包含變數占位符的提示字串     guild_id: 伺服器 ID（用於語言本地化）      Returns:     替換變數後的提示字串
  - `_get_system_variables(self) -> Dict[str, Any]`: 獲取系統變數字典  Returns:     系統變數字典
  - `_get_language(self, guild_id, message) -> str`: 取得語言設定
  - `debug_cache_state(self, guild_id, channel_id) -> Dict[str, Any]`: 快取狀態除錯（供管理員使用）  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID（可選）      Returns:     詳細的快取狀態報告
  - `get_diagnostics(self) -> Dict[str, Any]`: 取得診斷資訊  Returns:     診斷資訊字典
  - `handle_discord_interaction_cache_issues(self, interaction) -> Dict[str, Any]`: 處理 Discord 互動的快取問題（整合版）  Args:     interaction: Discord 互動物件      Returns:     處理結果報告
  - `reload_all_configs(self) -> bool`: 重新載入所有配置（用於 UI 介面）  Returns:     是否重新載入成功

## Functions

None

