# File: `addons/update/checker.py`

## Overview
This file belongs to the Addons Subsystem. Its core responsibility is to handle logic related to `checker.py`, providing vital integrations within the PigPig bot ecosystem.
版本檢查器模組

負責檢查 GitHub 上的最新版本並與當前版本進行比較。

## Classes

### `VersionChecker`
版本檢查器

- **Attributes**:
  - `github_api_url` (`Any`): Internal instance state.
  - `current_version` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(github_config: Dict[Tuple]) -> Any`: 初始化版本檢查器
  - `_get_current_version() -> str`: 獲取當前版本
  - `check_for_updates() -> Dict[Tuple]`: 檢查是否有可用更新
  - `_compare_versions(current: str, latest: str) -> bool`: 比較版本號
  - `_get_error_result(error_message: str) -> Dict[Tuple]`: 獲取錯誤結果
  - `get_current_version() -> str`: 獲取當前版本


## Handwritten Context
# Checker Module

**File:** [`addons/update/checker.py`](addons/update/checker.py)

This module is responsible for checking for new versions of the bot on GitHub. It compares the local version with the latest release available in the repository.

## `VersionChecker` Class

The `VersionChecker` class handles the logic for checking versions.

### `__init__(self, github_config: Dict[str, str])`

Initializes the `VersionChecker`.

*   **Parameters:**
    *   `github_config` (Dict[str, str]): A dictionary containing GitHub configuration, including the `api_url`.

### Methods

#### `async check_for_updates(self) -> Dict[str, any]`

Checks for available updates by querying the GitHub API.

*   **Returns:** A dictionary containing version information and the update status. The dictionary includes keys such as `current_version`, `latest_version`, `update_available`, `release_notes`, and `download_url`.

#### `get_current_version(self) -> str`

Retrieves the current version of the bot.

*   **Returns:** The current version string.

### Example Usage

```python
import asyncio
from addons.update.checker import VersionChecker

async def main():
    # Example GitHub configuration
    github_config = {
        "api_url": "https://api.github.com/repos/starpig1129/ai-discord-bot-PigPig/releases/latest"
    }

    checker = VersionChecker(github_config)
    update_info = await checker.check_for_updates()

    if update_info.get("update_available"):
        print(f"New version available: {update_info['latest_version']}")
        print(f"Release notes: {update_info['release_notes']}")
    else:
        print("You are using the latest version.")

if __name__ == "__main__":
    asyncio.run(main())