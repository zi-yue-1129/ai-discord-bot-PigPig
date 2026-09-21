# File: `addons/update/security.py`

## Overview
安全控制模組

負責權限驗證、備份管理和回滾機制。

## Classes

### `UpdatePermissionChecker`
更新權限檢查器

- **Attributes**:
  - `bot_owner_id` (`Any`): Attribute holding bot_owner_id data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__() -> Any`: 初始化權限檢查器
  - `check_update_permission(user_id: int) -> bool`: 檢查更新權限 - 僅限 Bot 擁有者
  - `check_status_permission(interaction: discord.Interaction) -> bool`: 檢查狀態查看權限 - 管理員或擁有者
  - `get_bot_owner_id() -> int`: 獲取 Bot 擁有者 ID

### `BackupManager`
備份管理器

- **Attributes**:
  - `backup_dir` (`Any`): Attribute holding backup_dir data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(backup_dir: str) -> Any`: 初始化備份管理器
  - `create_backup(protected_files: Optional[List[str]]) -> str`: 創建當前版本備份
  - `_backup_directory_safely(source_dir: str, dest_dir: str, backup_root: str) -> None`: 安全地備份目錄，避免備份目錄本身造成無限遞歸
  - `rollback_to_backup(backup_id: str) -> bool`: 回滾到指定備份
  - `list_backups() -> List[dict]`: 列出所有可用的備份
  - `cleanup_old_backups(max_backups: int) -> None`: 清理過期備份
  - `get_backup_size(backup_id: str) -> int`: 獲取備份大小

### `ConfigProtector`
配置檔案保護器

- **Attributes**:
  - `logger` (`Any`): Attribute holding logger data.
  - `protected_files` (`Any`): Attribute holding protected_files data.

- **Methods**:
  - `__init__() -> Any`: 初始化配置保護器
  - `backup_configs(backup_path: str) -> bool`: 備份配置檔案
  - `restore_configs(backup_path: str) -> bool`: 恢復配置檔案
  - `verify_configs() -> bool`: 驗證配置檔案完整性

## Functions

No top-level functions defined.
