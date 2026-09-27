# File: `cogs/system_prompt/data_validator.py`

## Overview
系統提示數據驗證助手

提供額外的數據一致性檢查和驗證功能

## Classes

### `SystemPromptDataValidator`
系統提示數據驗證器

- **Attributes**:
  - `data_dir` (`Any`): Instance attribute for data_dir.

- **Methods**:
  - `__init__(data_dir) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `Path`.
  - `validate_config_consistency(guild_id, channel_id) -> Dict[...]`: 驗證配置一致性
  - `fix_inconsistent_data(guild_id, channel_id) -> bool`: 修復不一致的數據
  - `get_module_comparison(guild_id, channel_id, expected_modules) -> Dict[...]`: 比較期望的模組與實際存儲的模組
