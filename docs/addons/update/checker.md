# File: `addons/update/checker.py`

## Overview
版本檢查器模組

負責檢查 GitHub 上的最新版本並與當前版本進行比較。

## Classes

### `VersionChecker`
版本檢查器

- **Attributes**:
  - `github_api_url` (`Any`): Instance attribute for github_api_url.
  - `current_version` (`Any`): Instance attribute for current_version.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(github_config) -> Any`: 初始化版本檢查器
  - `_get_current_version() -> str`: 獲取當前版本
  - `check_for_updates() -> Dict[...]`: 檢查是否有可用更新
  - `_compare_versions(current, latest) -> bool`: 比較版本號
  - `_get_error_result(error_message) -> Dict[...]`: 獲取錯誤結果
  - `get_current_version() -> str`: 獲取當前版本
