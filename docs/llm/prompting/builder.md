# File: `llm/prompting/builder.py`

## Overview
The `PromptBuilder` class is responsible for constructing dynamic system prompts for the LLM system. It processes YAML configuration files, handles language localization, manages variable substitutions, and provides flexible prompt generation capabilities.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `builder.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `PromptBuilder`
提示建構器

- **Attributes**:
  - `logger` (`Any`): Internal instance state.
  - `module_titles` (`Any`): Internal instance state.

- **Methods**:
  - `__init__() -> Any`: 初始化建構器
  - `build_system_prompt(config: dict, modules: List[str]) -> str`: 建構完整的系統提示
  - `_format_module_content(module_config: dict, module_name: str) -> str`: 格式化模組內容。
  - `_process_nested_content(nested_config: dict, content_parts: List[str]) -> None`: 處理巢狀配置內容，跳過元資料 key。
  - `_get_module_title(module_name: str) -> str`: 取得模組標題
  - `apply_language_replacements(prompt: str, lang: str, lang_manager: Any, mappings: Optional[dict]) -> str`: Resolve explicit language placeholders and apply language mappings.
  - `format_with_variables(prompt: str, variables: dict, lang_manager: Any, guild_id: Union[Tuple]) -> str`: 格式化變數替換
  - `compose_modules(config: dict, module_list: List[str]) -> str`: 組合指定模組的提示內容
  - `validate_module_references(config: dict, modules: List[str]) -> List[str]`: 驗證模組引用，返回缺失的模組列表
  - `get_module_summary(config: dict, module_name: str) -> Optional[str]`: 取得模組的摘要描述
  - `build_partial_prompt(config: dict, modules: List[str], max_length: Optional[int]) -> str`: 建構部分提示（用於預覽或測試）
