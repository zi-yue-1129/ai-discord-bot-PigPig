# File: `llm/prompting/builder.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `builder` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `PromptBuilder`
提示建構器

- **Attributes**:
  - `logger` (`Any`): Instance attribute for logger.
  - `module_titles` (`Any`): Instance attribute for module_titles.

- **Methods**:
  - `__init__() -> Any`: 初始化建構器
  - `build_system_prompt(config, modules) -> str`: 建構完整的系統提示
  - `_format_module_content(module_config, module_name) -> str`: 格式化模組內容。
  - `_process_nested_content(nested_config, content_parts) -> None`: 處理巢狀配置內容，跳過元資料 key。
  - `_get_module_title(module_name) -> str`: 取得模組標題
  - `apply_language_replacements(prompt, lang, lang_manager, mappings) -> str`: Resolve explicit language placeholders and apply language mappings.
  - `format_with_variables(prompt, variables, lang_manager, guild_id) -> str`: 格式化變數替換
  - `compose_modules(config, module_list) -> str`: 組合指定模組的提示內容
  - `validate_module_references(config, modules) -> List[...]`: 驗證模組引用，返回缺失的模組列表
  - `get_module_summary(config, module_name) -> Optional[...]`: 取得模組的摘要描述
  - `build_partial_prompt(config, modules, max_length) -> str`: 建構部分提示（用於預覽或測試）
