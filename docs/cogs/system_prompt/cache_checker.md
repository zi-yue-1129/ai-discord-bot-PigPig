# File: `cogs/system_prompt/cache_checker.py`

## Overview
快取一致性檢查工具

提供快取系統的一致性檢查和修復功能

## Classes

### `CacheConsistencyChecker`
快取一致性檢查器

- **Attributes**:
  - `cache_manager` (`Any`): Instance attribute cache_manager

- **Methods**:
  - `check_cache_consistency(self, guild_id, channel_id, expected_content) -> Dict[str, Any]`: 檢查快取一致性  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID     expected_content: 期望的內容      Returns:     檢查結果
  - `force_cache_refresh(self, guild_id, channel_id) -> bool`: 強制重新整理快取  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID      Returns:     是否成功
  - `get_cache_statistics(self) -> Dict[str, Any]`: 取得快取統計資訊

## Functions

None
