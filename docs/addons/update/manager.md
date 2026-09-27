# File: `addons/update/manager.py`

## Overview
核心更新管理器模組

整合所有更新相關功能，提供統一的更新管理介面。

## Classes

### `UpdateStatusTracker`
更新狀態追蹤器

- **Attributes**:
  - `current_status` (`Any`): Instance attribute for current_status.
  - `progress` (`Any`): Instance attribute for progress.
  - `current_operation` (`Any`): Instance attribute for current_operation.
  - `start_time` (`Any`): Instance attribute for start_time.
  - `last_check_time` (`Any`): Instance attribute for last_check_time.
  - `error_message` (`Any`): Instance attribute for error_message.

- **Methods**:
  - `__init__() -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `update_status(status, progress, operation) -> Any`: 更新狀態
  - `set_error(error_message) -> Any`: 設定錯誤狀態
  - `reset() -> Any`: 重置狀態

### `UpdateLogger`
更新日誌管理器

- **Attributes**:
  - `log_dir` (`Any`): Instance attribute for log_dir.
  - `logger` (`Any`): Instance attribute for logger.
  - `log_file` (`Any`): Instance attribute for log_file.
  - `current_log` (`Any`): Instance attribute for current_log.

- **Methods**:
  - `__init__(log_dir) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `get_logger` and `makedirs`.
  - `start_log(event_type, trigger_type, user_id) -> Any`: 開始記錄更新事件
  - `update_log(**kwargs) -> Any`: 更新日誌內容
  - `finish_log(status, error_message) -> Any`: 完成日誌記錄
  - `_write_log() -> Any`: 寫入日誌檔案

### `UpdateManager`
核心更新管理器

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `logger` (`Any`): Instance attribute for logger.
  - `update_settings` (`Any`): Instance attribute for update_settings.
  - `config` (`Any`): Instance attribute for config.
  - `version_checker` (`Any`): Instance attribute for version_checker.
  - `downloader` (`Any`): Instance attribute for downloader.
  - `permission_checker` (`Any`): Instance attribute for permission_checker.
  - `backup_manager` (`Any`): Instance attribute for backup_manager.
  - `config_protector` (`Any`): Instance attribute for config_protector.
  - `notifier` (`Any`): Instance attribute for notifier.
  - `restart_manager` (`Any`): Instance attribute for restart_manager.
  - `status_tracker` (`Any`): Instance attribute for status_tracker.
  - `update_logger` (`Any`): Instance attribute for update_logger.
  - `_update_lock` (`Any`): Instance attribute for _update_lock.

- **Methods**:
  - `__init__(bot) -> Any`: 初始化更新管理器
  - `check_for_updates() -> Dict[...]`: 檢查更新
  - `execute_update(interaction, force) -> Dict[...]`: 執行更新流程
  - `_install_update(download_path, version) -> bool`: 安裝更新
  - `_verify_installation() -> bool`: 驗證安裝是否成功
  - `_start_auto_check() -> Any`: 啟動自動檢查
  - `get_status() -> Dict[...]`: 獲取更新系統狀態
  - `post_restart_initialization() -> Any`: 重啟後初始化
