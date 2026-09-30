# File: `addons/update/security.py`

## Overview
安全控制模組

負責權限驗證、備份管理和回滾機制。

## Classes

### `UpdatePermissionChecker`
更新權限檢查器

- **Attributes**:
  - `bot_owner_id` (`Any`): Instance attribute bot_owner_id
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `check_update_permission(self, user_id) -> bool`: 檢查更新權限 - 僅限 Bot 擁有者  Args:     user_id: 使用者 ID      Returns:     是否有更新權限
  - `check_status_permission(self, interaction) -> bool`: 檢查狀態查看權限 - 管理員或擁有者  Args:     interaction: Discord 互動物件      Returns:     是否有查看狀態權限
  - `get_bot_owner_id(self) -> int`: 獲取 Bot 擁有者 ID  Returns:     Bot 擁有者 ID

### `BackupManager`
備份管理器

- **Attributes**:
  - `backup_dir` (`Any`): Instance attribute backup_dir
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `create_backup(self, protected_files) -> str`: 創建當前版本備份  Args:     protected_files: 需要保護的檔案列表      Returns:     備份 ID      Raises:     Exception: 備份過程中的錯誤
  - `_backup_directory_safely(self, source_dir, dest_dir, backup_root) -> None`: 安全地備份目錄，避免備份目錄本身造成無限遞歸  Args:     source_dir: 來源目錄路徑     dest_dir: 目標目錄路徑     backup_root: 備份根目錄路徑
  - `rollback_to_backup(self, backup_id) -> bool`: 回滾到指定備份  Args:     backup_id: 備份 ID      Returns:     回滾是否成功
  - `list_backups(self) -> List[dict]`: 列出所有可用的備份  Returns:     備份資訊列表
  - `cleanup_old_backups(self, max_backups) -> None`: 清理過期備份  Args:     max_backups: 最大保留備份數量
  - `get_backup_size(self, backup_id) -> int`: 獲取備份大小  Args:     backup_id: 備份 ID      Returns:     備份大小（bytes）

### `ConfigProtector`
配置檔案保護器

- **Attributes**:
  - `logger` (`Any`): Instance attribute logger
  - `protected_files` (`Any`): Instance attribute protected_files

- **Methods**:
  - `backup_configs(self, backup_path) -> bool`: 備份配置檔案  Args:     backup_path: 備份路徑      Returns:     備份是否成功
  - `restore_configs(self, backup_path) -> bool`: 恢復配置檔案  Args:     backup_path: 備份路徑      Returns:     恢復是否成功
  - `verify_configs(self) -> bool`: 驗證配置檔案完整性  Returns:     驗證是否通過

## Functions

None

