# File: `llm/prompting/builder.py`

## Overview
This file is part of the llm subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `PromptBuilder`
提示建構器

- **Attributes**:
  - `logger` (`Any`): Attribute holding logger data.
  - `module_titles` (`Any`): Attribute holding module_titles data.

- **Methods**:
  - `__init__() -> Any`: 初始化建構器
  - `build_system_prompt(config: dict, modules: List[str]) -> str`: 建構完整的系統提示
  - `_format_module_content(module_config: dict, module_name: str) -> str`: 格式化模組內容。
  - `_process_nested_content(nested_config: dict, content_parts: List[str]) -> None`: 處理巢狀配置內容，跳過元資料 key。
  - `_get_module_title(module_name: str) -> str`: 取得模組標題
  - `apply_language_replacements(prompt: str, lang: str, lang_manager, mappings: Optional[dict]) -> str`: Resolve explicit language placeholders and apply language mappings.
  - `format_with_variables(prompt: str, variables: dict, lang_manager, guild_id: Union[Tuple[str, None]]) -> str`: 格式化變數替換
  - `compose_modules(config: dict, module_list: List[str]) -> str`: 組合指定模組的提示內容
  - `validate_module_references(config: dict, modules: List[str]) -> List[str]`: 驗證模組引用，返回缺失的模組列表
  - `get_module_summary(config: dict, module_name: str) -> Optional[str]`: 取得模組的摘要描述
  - `build_partial_prompt(config: dict, modules: List[str], max_length: Optional[int]) -> str`: 建構部分提示（用於預覽或測試）

## Functions

No top-level functions defined.
