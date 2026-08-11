# File: `cogs/system_prompt/data_validator.py`

## Overview
系統提示數據驗證助手

提供額外的數據一致性檢查和驗證功能

## Classes

### `SystemPromptDataValidator`
系統提示數據驗證器

- **Attributes**:
  - `data_dir` (`Any`): Instance attribute managing data_dir.

- **Methods**:
  - `validate_config_consistency(guild_id, channel_id) -> Dict[Tuple[str, Any]]`: 驗證配置一致性  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID      Returns:     驗證結果
  - `fix_inconsistent_data(guild_id, channel_id) -> bool`: 修復不一致的數據  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID      Returns:     是否修復成功
  - `get_module_comparison(guild_id, channel_id, expected_modules) -> Dict[Tuple[str, Any]]`: 比較期望的模組與實際存儲的模組  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID     expected_modules: 期望的模組數據      Returns:     比較結果
