# File: `addons/update/checker.py`

## Overview
版本檢查器模組

負責檢查 GitHub 上的最新版本並與當前版本進行比較。

## Classes

### `VersionChecker`
版本檢查器

- **Attributes**:
  - `github_api_url` (`Any`): Instance attribute github_api_url
  - `current_version` (`Any`): Instance attribute current_version
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `_get_current_version(self) -> str`: 獲取當前版本  Returns:     當前版本字串
  - `check_for_updates(self) -> Dict[str, any]`: 檢查是否有可用更新  Returns:     包含版本資訊和更新狀態的字典
  - `_compare_versions(self, current, latest) -> bool`: 比較版本號  Args:     current: 當前版本     latest: 最新版本      Returns:     如果有新版本可用則返回 True
  - `_get_error_result(self, error_message) -> Dict[str, any]`: 獲取錯誤結果  Args:     error_message: 錯誤訊息      Returns:     錯誤結果字典
  - `get_current_version(self) -> str`: 獲取當前版本  Returns:     當前版本字串

## Functions

None

