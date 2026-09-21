# File: `addons/update/checker.py`

## Overview
版本檢查器模組

負責檢查 GitHub 上的最新版本並與當前版本進行比較。

## Classes

### `VersionChecker`
版本檢查器

- **Attributes**:
  - `github_api_url` (`Any`): Attribute holding github_api_url data.
  - `current_version` (`Any`): Attribute holding current_version data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(github_config: Dict[Tuple[str, str]]) -> Any`: 初始化版本檢查器
  - `_get_current_version() -> str`: 獲取當前版本
  - `check_for_updates() -> Dict[Tuple[str, any]]`: 檢查是否有可用更新
  - `_compare_versions(current: str, latest: str) -> bool`: 比較版本號
  - `_get_error_result(error_message: str) -> Dict[Tuple[str, any]]`: 獲取錯誤結果
  - `get_current_version() -> str`: 獲取當前版本

## Functions

No top-level functions defined.
