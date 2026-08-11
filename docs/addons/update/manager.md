# File: `addons/update/manager.py`

## Overview
核心更新管理器模組

整合所有更新相關功能，提供統一的更新管理介面。

## Classes

### `UpdateStatusTracker`
更新狀態追蹤器

- **Attributes**:
  - `current_status` (`Any`): Instance attribute managing current_status.
  - `progress` (`Any`): Instance attribute managing progress.
  - `current_operation` (`Any`): Instance attribute managing current_operation.
  - `start_time` (`Any`): Instance attribute managing start_time.
  - `last_check_time` (`Any`): Instance attribute managing last_check_time.
  - `error_message` (`Any`): Instance attribute managing error_message.

- **Methods**:
  - `update_status(status, progress, operation) -> Any`: 更新狀態
  - `set_error(error_message) -> Any`: 設定錯誤狀態
  - `reset() -> Any`: 重置狀態

### `UpdateLogger`
更新日誌管理器

- **Attributes**:
  - `log_dir` (`Any`): Instance attribute managing log_dir.
  - `logger` (`Any`): Instance attribute managing logger.
  - `log_file` (`Any`): Instance attribute managing log_file.
  - `current_log` (`Any`): Instance attribute managing current_log.

- **Methods**:
  - `start_log(event_type, trigger_type, user_id) -> Any`: 開始記錄更新事件
  - `update_log(**kwargs) -> Any`: 更新日誌內容
  - `finish_log(status, error_message) -> Any`: 完成日誌記錄

### `UpdateManager`
核心更新管理器

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `logger` (`Any`): Instance attribute managing logger.
  - `update_settings` (`Any`): Instance attribute managing update_settings.
  - `config` (`Any`): Instance attribute managing config.
  - `version_checker` (`Any`): Instance attribute managing version_checker.
  - `downloader` (`Any`): Instance attribute managing downloader.
  - `permission_checker` (`Any`): Instance attribute managing permission_checker.
  - `backup_manager` (`Any`): Instance attribute managing backup_manager.
  - `config_protector` (`Any`): Instance attribute managing config_protector.
  - `notifier` (`Any`): Instance attribute managing notifier.
  - `restart_manager` (`Any`): Instance attribute managing restart_manager.
  - `status_tracker` (`Any`): Instance attribute managing status_tracker.
  - `update_logger` (`Any`): Instance attribute managing update_logger.
  - `_update_lock` (`Any`): Instance attribute managing _update_lock.

- **Methods**:
  - `check_for_updates() -> Dict[Tuple[str, Any]]`: 檢查更新
  - `execute_update(interaction, force) -> Dict[Tuple[str, Any]]`: 執行更新流程  Args:     interaction: Discord 互動物件     force: 是否強制更新      Returns:     更新結果字典
  - `get_status() -> Dict[Tuple[str, Any]]`: 獲取更新系統狀態
  - `post_restart_initialization() -> Any`: 重啟後初始化

