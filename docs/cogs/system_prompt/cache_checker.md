# File: `cogs/system_prompt/cache_checker.py`

## Overview
快取一致性檢查工具

提供快取系統的一致性檢查和修復功能

## Classes

### `CacheConsistencyChecker`
快取一致性檢查器

- **Attributes**:
  - `cache_manager` (`Any`): Instance attribute for cache_manager.

- **Methods**:
  - `__init__(cache_manager) -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `check_cache_consistency(guild_id, channel_id, expected_content) -> Dict[...]`: 檢查快取一致性
  - `force_cache_refresh(guild_id, channel_id) -> bool`: 強制重新整理快取
  - `get_cache_statistics() -> Dict[...]`: 取得快取統計資訊
