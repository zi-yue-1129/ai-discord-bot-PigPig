# File: `addons/update/security.py`

## Overview
This file belongs to the Addons Subsystem. Its core responsibility is to handle logic related to `security.py`, providing vital integrations within the PigPig bot ecosystem.
安全控制模組

負責權限驗證、備份管理和回滾機制。

## Classes

### `UpdatePermissionChecker`
更新權限檢查器

- **Attributes**:
  - `bot_owner_id` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__() -> Any`: 初始化權限檢查器
  - `check_update_permission(user_id: int) -> bool`: 檢查更新權限 - 僅限 Bot 擁有者
  - `check_status_permission(interaction: discord.Interaction) -> bool`: 檢查狀態查看權限 - 管理員或擁有者
  - `get_bot_owner_id() -> int`: 獲取 Bot 擁有者 ID

### `BackupManager`
備份管理器

- **Attributes**:
  - `backup_dir` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

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
  - `logger` (`Any`): Internal instance state.
  - `protected_files` (`Any`): Internal instance state.

- **Methods**:
  - `__init__() -> Any`: 初始化配置保護器
  - `backup_configs(backup_path: str) -> bool`: 備份配置檔案
  - `restore_configs(backup_path: str) -> bool`: 恢復配置檔案
  - `verify_configs() -> bool`: 驗證配置檔案完整性


## Handwritten Context
# Security Module

**File:** [`addons/update/security.py`](addons/update/security.py)

This module provides security features for the update process, including permission checking, file backups, and configuration protection.

## `UpdatePermissionChecker` Class

This class is used to verify if a user has the necessary permissions to perform update-related actions.

### `__init__(self)`

Initializes the permission checker by loading the bot owner's ID from the environment variables.

### Methods

#### `check_update_permission(self, user_id: int) -> bool`

Checks if a user has permission to execute an update. Only the bot owner is permitted.

*   **Parameters:**
    *   `user_id` (int): The Discord ID of the user.
*   **Returns:** `True` if the user is the bot owner, `False` otherwise.

#### `check_status_permission(self, interaction: discord.Interaction) -> bool`

Checks if a user has permission to view the update system's status. Permitted for server administrators and the bot owner.

*   **Parameters:**
    *   `interaction` (discord.Interaction): The interaction object from a command.
*   **Returns:** `True` if the user has permission, `False` otherwise.

## `BackupManager` Class

This class manages the creation, restoration, and cleanup of backups.

### `__init__(self, backup_dir: str = "data/backups")`

Initializes the backup manager.

*   **Parameters:**
    *   `backup_dir` (str): The directory where backups are stored. Defaults to `"data/backups"`.

### Methods

#### `create_backup(self, protected_files: Optional[List[str]] = None) -> str`

Creates a backup of the current bot state, including specified protected files and directories.

*   **Parameters:**
    *   `protected_files` (Optional[List[str]]): A list of files and directories to include in the backup.
*   **Returns:** The unique ID of the created backup.
*   **Raises:** `Exception` if the backup process fails.

#### `rollback_to_backup(self, backup_id: str) -> bool`

Restores the bot's files from a specified backup.

*   **Parameters:**
    *   `backup_id` (str): The ID of the backup to restore.
*   **Returns:** `True` if the rollback is successful, `False` otherwise.

#### `list_backups(self) -> List[dict]`

Lists all available backups.

*   **Returns:** A list of dictionaries, where each dictionary contains information about a backup.

#### `cleanup_old_backups(self, max_backups: int = 5) -> None`

Deletes the oldest backups, keeping a specified number of recent backups.

*   **Parameters:**
    *   `max_backups` (int): The maximum number of backups to retain.

## `ConfigProtector` Class

This class is dedicated to backing up and restoring critical configuration files during the update process.

### Methods

#### `backup_configs(self, backup_path: str) -> bool`

Backs up critical configuration files to a specified path.

*   **Parameters:**
    *   `backup_path` (str): The path where the configuration backup will be stored.
*   **Returns:** `True` if successful, `False` otherwise.

#### `restore_configs(self, backup_path: str) -> bool`

Restores configuration files from a backup.

*   **Parameters:**
    *   `backup_path` (str): The path of the configuration backup.
*   **Returns:** `True` if successful, `False` otherwise.

#### `verify_configs(self) -> bool`

Verifies the integrity of critical configuration files (e.g., checks if JSON files are valid).

*   **Returns:** `True` if all configurations are valid, `False` otherwise.