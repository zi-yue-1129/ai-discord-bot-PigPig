# File: `cogs/system_prompt/cache_checker.py`

## Overview
快取一致性檢查工具

## Classes

### `CacheConsistencyChecker`
快取一致性檢查器

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(cache_manager) -> Any`: No description provided.
  - `check_cache_consistency(guild_id: str, channel_id: str, expected_content: str) -> Dict[Tuple[str, Any]]`: 檢查快取一致性
  - `force_cache_refresh(guild_id: str, channel_id: str) -> bool`: 強制重新整理快取
  - `get_cache_statistics() -> Dict[Tuple[str, Any]]`: 取得快取統計資訊

## Functions

No module-level functions defined in this file.
