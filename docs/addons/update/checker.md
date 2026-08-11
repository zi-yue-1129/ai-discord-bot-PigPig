# File: `addons/update/checker.py`

## Overview
版本檢查器模組

負責檢查 GitHub 上的最新版本並與當前版本進行比較。

## Classes

### `VersionChecker`
版本檢查器

- **Attributes**:
  - `github_api_url` (`Any`): Instance attribute managing github_api_url.
  - `current_version` (`Any`): Instance attribute managing current_version.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `check_for_updates() -> Dict[Tuple[str, any]]`: 檢查是否有可用更新  Returns:     包含版本資訊和更新狀態的字典
  - `get_current_version() -> str`: 獲取當前版本  Returns:     當前版本字串

