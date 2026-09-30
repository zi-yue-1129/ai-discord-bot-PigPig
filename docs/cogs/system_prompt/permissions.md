# File: `cogs/system_prompt/permissions.py`

## Overview
頻道系統提示管理模組的權限驗證器

提供完整的權限檢查和驗證邏輯，支援多層權限控制。

## Classes

### `PermissionValidator`
權限驗證器類別

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `can_modify_channel_prompt(self, user, channel, config) -> bool`: 檢查用戶是否可修改頻道提示  Args:     user: Discord 用戶     channel: 目標頻道     config: 頻道配置（可選）      Returns:     是否有權限
  - `can_modify_server_prompt(self, user, guild, config) -> bool`: 檢查用戶是否可修改伺服器提示  Args:     user: Discord 用戶     guild: 目標伺服器     config: 伺服器配置（可選）      Returns:     是否有權限
  - `can_view_prompt(self, user, channel) -> bool`: 檢查用戶是否可查看系統提示  Args:     user: Discord 用戶     channel: 目標頻道（可選）      Returns:     是否有權限
  - `get_user_permissions(self, user, guild, config) -> Dict[str, any]`: 取得用戶的詳細權限資訊  Args:     user: Discord 用戶     guild: Discord 伺服器     config: 配置檔案（可選）      Returns:     權限資訊字典
  - `validate_permission_or_raise(self, user, action, target, config) -> None`: 驗證權限，如果沒有權限則拋出例外  Args:     user: Discord 用戶     action: 操作類型 ('modify_channel', 'modify_server', 'view')     target: 目標物件（頻道或伺服器）     config: 配置檔案（可選）      Raises:     PermissionError: 當用戶沒有足夠權限時
  - `_is_bot_owner(self, user) -> bool`: 檢查是否為機器人擁有者
  - `_has_custom_permission(self, user, channel, config) -> bool`: 檢查是否有自訂頻道權限
  - `_has_server_level_permission(self, user, config) -> bool`: 檢查是否有伺服器級別的自訂權限
  - `_get_all_channels(self, guild) -> List[str]`: 取得伺服器所有文字頻道 ID
  - `_get_custom_permissions(self, user, config) -> Dict`: 取得自訂權限設定

## Functions

None

