# File: `cogs/system_prompt/permissions.py`

## Overview
頻道系統提示管理模組的權限驗證器

提供完整的權限檢查和驗證邏輯，支援多層權限控制。

## Classes

### `PermissionValidator`
權限驗證器類別

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(bot) -> Any`: 初始化權限驗證器
  - `can_modify_channel_prompt(user, channel, config) -> bool`: 檢查用戶是否可修改頻道提示
  - `can_modify_server_prompt(user, guild, config) -> bool`: 檢查用戶是否可修改伺服器提示
  - `can_view_prompt(user, channel) -> bool`: 檢查用戶是否可查看系統提示
  - `get_user_permissions(user, guild, config) -> Dict[...]`: 取得用戶的詳細權限資訊
  - `validate_permission_or_raise(user, action, target, config) -> None`: 驗證權限，如果沒有權限則拋出例外
  - `_is_bot_owner(user) -> bool`: 檢查是否為機器人擁有者
  - `_has_custom_permission(user, channel, config) -> bool`: 檢查是否有自訂頻道權限
  - `_has_server_level_permission(user, config) -> bool`: 檢查是否有伺服器級別的自訂權限
  - `_get_all_channels(guild) -> List[...]`: 取得伺服器所有文字頻道 ID
  - `_get_custom_permissions(user, config) -> Dict`: 取得自訂權限設定
