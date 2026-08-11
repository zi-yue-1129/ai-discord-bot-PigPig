# File: `cogs/system_prompt/cache_checker.py`

## Overview
快取一致性檢查工具

提供快取系統的一致性檢查和修復功能

## Classes

### `CacheConsistencyChecker`
快取一致性檢查器

- **Attributes**:
  - `cache_manager` (`Any`): Instance attribute managing cache_manager.

- **Methods**:
  - `check_cache_consistency(guild_id, channel_id, expected_content) -> Dict[Tuple[str, Any]]`: 檢查快取一致性  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID     expected_content: 期望的內容      Returns:     檢查結果
  - `force_cache_refresh(guild_id, channel_id) -> bool`: 強制重新整理快取  Args:     guild_id: 伺服器 ID     channel_id: 頻道 ID      Returns:     是否成功
  - `get_cache_statistics() -> Dict[Tuple[str, Any]]`: 取得快取統計資訊
