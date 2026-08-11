# File: `cogs/system_prompt/manager.py`

## Overview
Channel system prompt manager.

Provides core system prompt management functionality, including three-level inheritance,
caching system, and configuration management.

## Classes

### `SystemPromptCache`
System prompt cache manager.

- **Attributes**:
  - `ttl` (`Any`): Instance attribute managing ttl.

- **Methods**:
  - `get_cache_key(guild_id, channel_id, lang) -> str`: Generate cache key.
  - `get(guild_id, channel_id, lang) -> Optional[str]`: Get system prompt from cache.
  - `set(guild_id, channel_id, prompt, lang) -> None`: Set cache.
  - `invalidate(guild_id, channel_id) -> None`: Invalidate cache.
  - `clear_all() -> None`: Clear all cache.

### `PromptValidator`
System prompt validator.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.

- **Methods**:
  - `validate_prompt_content(content) -> Tuple[Tuple[bool, str]]`: Validate prompt content.  Args:     content: Prompt content.      Returns:     (is_valid, error_message)
  - `validate_modules(modules, guild_id) -> Tuple[Tuple[bool, str]]`: Validate module configuration.  Args:     modules: Module dictionary.     guild_id: Server ID (optional).      Returns:     (is_valid, error_message)

### `SystemPromptManager`
System prompt manager - Core coordinator.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `logger` (`Any`): Instance attribute managing logger.
  - `cache` (`Any`): Instance attribute managing cache.
  - `validator` (`Any`): Instance attribute managing validator.
  - `permission_validator` (`Any`): Instance attribute managing permission_validator.
  - `data_dir` (`Any`): Instance attribute managing data_dir.
  - `_prompt_manager` (`Any`): Instance attribute managing _prompt_manager.

- **Methods**:
  - `get_effective_prompt(channel_id, guild_id, message) -> Dict[Tuple[str, Any]]`: Get effective system prompt (integrated three-level inheritance).  Args:     channel_id: Channel ID.     guild_id: Server ID.     message: Discord message object (for language detection).      Returns:     Dictionary containing prompt content and source.
  - `get_channel_prompt_config(guild_id, channel_id) -> Optional[Dict[Tuple[str, Any]]]`: 取得指定頻道的原始系統提示設定。  這個方法會直接從設定檔中讀取並回傳該頻道的設定字典， 而不會進行繼承合併或變數替換。  Args:     guild_id: 伺服器 ID。     channel_id: 頻道 ID。  Returns:     包含頻道設定的字典，如果不存在則回傳 None。
  - `set_channel_prompt(guild_id, channel_id, prompt_data, user_id) -> bool`: 設定頻道系統提示  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID     prompt_data: 提示資料     user_id: 操作用戶 ID      Returns:     是否設定成功
  - `set_server_prompt(guild_id, prompt_data, user_id) -> bool`: 設定伺服器級別系統提示  Args:     guild_id: 伺服器 ID     prompt_data: 提示資料     user_id: 操作用戶 ID      Returns:     是否設定成功
  - `remove_channel_prompt(guild_id, channel_id) -> bool`: 移除頻道系統提示  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID      Returns:     是否移除成功
  - `remove_server_prompt(guild_id) -> bool`: 移除伺服器級別系統提示  Args:     guild_id: 伺服器 ID      Returns:     是否移除成功
  - `copy_channel_prompt(source_guild, source_channel, target_guild, target_channel) -> bool`: 複製頻道提示設定  Args:     source_guild: 來源伺服器 ID     source_channel: 來源頻道 ID     target_guild: 目標伺服器 ID     target_channel: 目標頻道 ID      Returns:     是否複製成功
  - `get_available_modules() -> List[str]`: 取得可覆蓋的 YAML 模組列表
  - `get_default_module_content(module_name) -> str`: 獲取指定模組的預設內容  Args:     module_name: 模組名稱      Returns:     模組的預設內容字串
  - `get_effective_full_prompt(channel_id, guild_id, for_editing) -> str`: 獲取當前有效的完整系統提示（用於直接編輯時顯示）  Args:     channel_id: 頻道 ID     guild_id: 伺服器 ID     for_editing: 是否用於編輯（如果是，返回未替換變數的版本）      Returns:     完整的有效系統提示內容
  - `get_module_descriptions(lang) -> Dict[Tuple[str, str]]`: 獲取模組說明字典  Args:     lang: 語言代碼      Returns:     模組名稱對應說明的字典
  - `clear_cache(guild_id, channel_id) -> None`: 清除快取（全面同步清除）  Args:     guild_id: 伺服器 ID（可選）     channel_id: 頻道 ID（可選）
  - `force_clear_all_caches(guild_id, channel_id, interaction) -> None`: 強制清除所有相關快取（整合版）- 異步版本  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID（可選）     interaction: Discord 互動物件（可選）
  - `reload_system_prompts(guild_id, channel_id) -> bool`: 重新載入系統提示配置（完整重新載入方案）  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID（可選）      Returns:     是否重新載入成功
  - `debug_cache_state(guild_id, channel_id) -> Dict[Tuple[str, Any]]`: 快取狀態除錯（供管理員使用）  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID（可選）      Returns:     詳細的快取狀態報告
  - `get_diagnostics() -> Dict[Tuple[str, Any]]`: 取得診斷資訊  Returns:     診斷資訊字典
  - `handle_discord_interaction_cache_issues(interaction) -> Dict[Tuple[str, Any]]`: 處理 Discord 互動的快取問題（整合版）  Args:     interaction: Discord 互動物件      Returns:     處理結果報告
  - `reload_all_configs() -> bool`: 重新載入所有配置（用於 UI 介面）  Returns:     是否重新載入成功

