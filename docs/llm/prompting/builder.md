# File: `llm/prompting/builder.py`

## Overview
This file is part of the LLM integration and orchestration pipeline and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `llm/prompting/builder.py`.

## Classes

### `PromptBuilder`
提示建構器

- **Attributes**:
  - `logger` (`Any`): Instance attribute logger
  - `module_titles` (`Any`): Instance attribute module_titles

- **Methods**:
  - `build_system_prompt(self, config, modules) -> str`: 建構完整的系統提示  追加診斷日誌：記錄 module_order、requested modules，以及每個模組是否存在於配置中。  Args:     config: 配置字典     modules: 要包含的模組列表      Returns:     組合後的完整系統提示
  - `_format_module_content(self, module_config, module_name) -> str`: 格式化模組內容。  Strategy: 1. `base` module: return `core_instruction` directly. 2. Modules with a `content` key: use that string directly.    The content is expected to contain its own ## markdown heading,    so no extra title prefix is added. 3. Fallback (no `content` key): collect from all non-metadata keys.    A title prefix is prepended using `module_titles`.
  - `_process_nested_content(self, nested_config, content_parts) -> None`: 處理巢狀配置內容，跳過元資料 key。
  - `_get_module_title(self, module_name) -> str`: 取得模組標題  Args:     module_name: 模組名稱      Returns:     模組標題
  - `apply_language_replacements(self, prompt, lang, lang_manager, mappings) -> str`: Resolve explicit language placeholders and apply language mappings.  Strategy: - Resolve placeholders of the form {{lang.<path>}} using LanguageManager translations. - Also handle single-brace forms {lang.<path>} which may appear after Python .format processing. - If mappings (YAML) are provided, apply them deterministically (exact replace) after placeholder resolution. - Keep behavior safe: any resolution error is reported via func.report_error and the original prompt is returned.  Args:     prompt: original prompt text     lang: language code (e.g., "zh_TW")     lang_manager: LanguageManager instance     mappings: optional dict mapping source strings to translation paths               (e.g. {"Always answer in Traditional Chinese": "system.chat_bot.language.answer_in"})  Returns:     prompt with replacements applied
  - `format_with_variables(self, prompt, variables, lang_manager, guild_id) -> str`: 格式化變數替換  Args:     prompt: 包含變數的提示模板     variables: 變數字典     lang_manager: LanguageManager instance for language replacements     guild_id: Server ID for language-specific translations      Returns:     替換變數後的提示
  - `compose_modules(self, config, module_list) -> str`: 組合指定模組的提示內容  Args:     config: 配置字典     module_list: 要組合的模組列表      Returns:     組合後的提示內容
  - `validate_module_references(self, config, modules) -> List[str]`: 驗證模組引用，返回缺失的模組列表  Args:     config: 配置字典     modules: 要驗證的模組列表      Returns:     缺失的模組名稱列表
  - `get_module_summary(self, config, module_name) -> Optional[str]`: 取得模組的摘要描述  Args:     config: 配置字典     module_name: 模組名稱      Returns:     模組摘要，如果模組不存在則返回 None
  - `build_partial_prompt(self, config, modules, max_length) -> str`: 建構部分提示（用於預覽或測試）  Args:     config: 配置字典     modules: 模組列表     max_length: 最大長度限制      Returns:     部分提示內容

## Functions

None

