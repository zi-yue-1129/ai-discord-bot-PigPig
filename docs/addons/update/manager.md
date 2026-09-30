# File: `addons/update/manager.py`

## Overview
核心更新管理器模組

整合所有更新相關功能，提供統一的更新管理介面。

## Classes

### `UpdateStatusTracker`
更新狀態追蹤器

- **Attributes**:
  - `current_status` (`Any`): Instance attribute current_status
  - `progress` (`Any`): Instance attribute progress
  - `current_operation` (`Any`): Instance attribute current_operation
  - `start_time` (`Any`): Instance attribute start_time
  - `last_check_time` (`Any`): Instance attribute last_check_time
  - `error_message` (`Any`): Instance attribute error_message

- **Methods**:
  - `update_status(self, status, progress, operation) -> Any`: 更新狀態
  - `set_error(self, error_message) -> Any`: 設定錯誤狀態
  - `reset(self) -> Any`: 重置狀態

### `UpdateLogger`
更新日誌管理器

- **Attributes**:
  - `log_dir` (`Any`): Instance attribute log_dir
  - `logger` (`Any`): Instance attribute logger
  - `log_file` (`Any`): Instance attribute log_file
  - `current_log` (`Any`): Instance attribute current_log

- **Methods**:
  - `start_log(self, event_type, trigger_type, user_id) -> Any`: 開始記錄更新事件
  - `update_log(self, **kwargs) -> Any`: 更新日誌內容
  - `finish_log(self, status, error_message) -> Any`: 完成日誌記錄
  - `_write_log(self) -> Any`: 寫入日誌檔案

### `UpdateManager`
核心更新管理器

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `logger` (`Any`): Instance attribute logger
  - `update_settings` (`Any`): Instance attribute update_settings
  - `config` (`Any`): Instance attribute config
  - `version_checker` (`Any`): Instance attribute version_checker
  - `downloader` (`Any`): Instance attribute downloader
  - `permission_checker` (`Any`): Instance attribute permission_checker
  - `backup_manager` (`Any`): Instance attribute backup_manager
  - `config_protector` (`Any`): Instance attribute config_protector
  - `notifier` (`Any`): Instance attribute notifier
  - `restart_manager` (`Any`): Instance attribute restart_manager
  - `status_tracker` (`Any`): Instance attribute status_tracker
  - `update_logger` (`Any`): Instance attribute update_logger
  - `_update_lock` (`Any`): Instance attribute _update_lock

- **Methods**:
  - `check_for_updates(self) -> Dict[str, Any]`: 檢查更新
  - `execute_update(self, interaction, force) -> Dict[str, Any]`: 執行更新流程  Args:     interaction: Discord 互動物件     force: 是否強制更新      Returns:     更新結果字典
  - `_install_update(self, download_path, version) -> bool`: 安裝更新  Args:     download_path: 下載檔案路徑     version: 版本號      Returns:     安裝是否成功
  - `_verify_installation(self) -> bool`: 驗證安裝是否成功
  - `_start_auto_check(self) -> Any`: 啟動自動檢查
  - `get_status(self) -> Dict[str, Any]`: 獲取更新系統狀態
  - `post_restart_initialization(self) -> Any`: 重啟後初始化

## Functions

None

