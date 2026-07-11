# File: `addons/update/manager.py`

## Overview
This file belongs to the Addons Subsystem. Its core responsibility is to handle logic related to `manager.py`, providing vital integrations within the PigPig bot ecosystem.
核心更新管理器模組

整合所有更新相關功能，提供統一的更新管理介面。

## Classes

### `UpdateStatusTracker`
更新狀態追蹤器

- **Attributes**:
  - `current_status` (`Any`): Internal instance state.
  - `progress` (`Any`): Internal instance state.
  - `current_operation` (`Any`): Internal instance state.
  - `start_time` (`Any`): Internal instance state.
  - `last_check_time` (`Any`): Internal instance state.
  - `error_message` (`Any`): Internal instance state.

- **Methods**:
  - `__init__() -> Any`: Performs internal processing logic.
  - `update_status(status: str, progress: int, operation: str) -> Any`: 更新狀態
  - `set_error(error_message: str) -> Any`: 設定錯誤狀態
  - `reset() -> Any`: 重置狀態

### `UpdateLogger`
更新日誌管理器

- **Attributes**:
  - `log_dir` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.
  - `log_file` (`Any`): Internal instance state.
  - `current_log` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(log_dir: str) -> Any`: Performs internal processing logic.
  - `start_log(event_type: str, trigger_type: str, user_id: Optional[int]) -> Any`: 開始記錄更新事件
  - `update_log() -> Any`: 更新日誌內容
  - `finish_log(status: str, error_message: Optional[str]) -> Any`: 完成日誌記錄
  - `_write_log() -> Any`: 寫入日誌檔案

### `UpdateManager`
核心更新管理器

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.
  - `update_settings` (`Any`): Internal instance state.
  - `config` (`Any`): Internal instance state.
  - `version_checker` (`Any`): Internal instance state.
  - `downloader` (`Any`): Internal instance state.
  - `permission_checker` (`Any`): Internal instance state.
  - `backup_manager` (`Any`): Internal instance state.
  - `config_protector` (`Any`): Internal instance state.
  - `notifier` (`Any`): Internal instance state.
  - `restart_manager` (`Any`): Internal instance state.
  - `status_tracker` (`Any`): Internal instance state.
  - `update_logger` (`Any`): Internal instance state.
  - `_update_lock` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any) -> Any`: 初始化更新管理器
  - `check_for_updates() -> Dict[Tuple]`: 檢查更新
  - `execute_update(interaction: Any, force: bool) -> Dict[Tuple]`: 執行更新流程
  - `_install_update(download_path: str, version: str) -> bool`: 安裝更新
  - `_verify_installation() -> bool`: 驗證安裝是否成功
  - `_start_auto_check() -> Any`: 啟動自動檢查
  - `get_status() -> Dict[Tuple]`: 獲取更新系統狀態
  - `post_restart_initialization() -> Any`: 重啟後初始化


## Handwritten Context
# Manager Module

**File:** [`addons/update/manager.py`](addons/update/manager.py)

This is the core module of the update system. The `UpdateManager` class orchestrates the entire update process, integrating all other components of the system, such as the version checker, downloader, and notifier.

## `UpdateManager` Class

This class provides a unified interface for managing the full update lifecycle.

### `__init__(self, bot)`

Initializes the `UpdateManager` and all its components.

*   **Parameters:**
    *   `bot`: The instance of the Discord bot.

### Methods

#### `async check_for_updates(self) -> Dict[str, Any]`

Checks for available updates.

*   **Returns:** A dictionary containing version information. See [`VersionChecker.check_for_updates()`](./checker.md#async-check_for_updates-self---dictstr-any) for details.

#### `async execute_update(self, interaction=None, force: bool = False) -> Dict[str, Any]`

Executes the full update process. This is a comprehensive workflow that includes:
1.  Checking for updates.
2.  Creating a backup (if enabled).
3.  Downloading the new version.
4.  Installing the update.
5.  Cleaning up old backups and downloaded files.
6.  Notifying the owner of the result.
7.  Initiating a graceful restart.

*   **Parameters:**
    *   `interaction` (Optional): The Discord interaction object that triggered the update.
    *   `force` (bool): If `True`, the update will be attempted even if no new version is detected.
*   **Returns:** A dictionary containing the results of the update, including a `success` flag and other relevant details.

#### `get_status(self) -> Dict[str, Any]`

Gets the current status of the update system.

*   **Returns:** A dictionary with status information, such as `status`, `progress`, `operation`, and `current_version`.

#### `async post_restart_initialization(self)`

Performs necessary checks and initializations after the bot has restarted. This is typically called once upon bot startup.

## `UpdateStatusTracker` Class

This class tracks the real-time status of the update process.

### Properties

*   `current_status` (str): The current status (e.g., "idle", "checking", "downloading", "error").
*   `progress` (int): The progress percentage of the current operation.
*   `current_operation` (str): A description of the current operation.
*   `error_message` (Optional[str]): An error message if the process has failed.

## `UpdateLogger` Class

This class logs all update events to a file for auditing and debugging purposes.

### `__init__(self, log_dir: str = "data/update_logs")`

Initializes the logger.

*   **Parameters:**
    *   `log_dir` (str): The directory where update logs are stored.