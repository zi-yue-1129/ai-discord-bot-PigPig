# File: `cogs/system_prompt/permissions.py`

## Overview
頻道系統提示管理模組的權限驗證器

提供完整的權限檢查和驗證邏輯，支援多層權限控制。

## Classes

### `PermissionValidator`
權限驗證器類別

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(bot: discord.Client) -> Any`: 初始化權限驗證器
  - `can_modify_channel_prompt(user: discord.Member, channel: discord.TextChannel, config: Optional[Dict]) -> bool`: 檢查用戶是否可修改頻道提示
  - `can_modify_server_prompt(user: discord.Member, guild: discord.Guild, config: Optional[Dict]) -> bool`: 檢查用戶是否可修改伺服器提示
  - `can_view_prompt(user: discord.Member, channel: Optional[discord.TextChannel]) -> bool`: 檢查用戶是否可查看系統提示
  - `get_user_permissions(user: discord.Member, guild: discord.Guild, config: Optional[Dict]) -> Dict[Tuple[str, any]]`: 取得用戶的詳細權限資訊
  - `validate_permission_or_raise(user: discord.Member, action: str, target: any, config: Optional[Dict]) -> None`: 驗證權限，如果沒有權限則拋出例外
  - `_is_bot_owner(user: discord.Member) -> bool`: 檢查是否為機器人擁有者
  - `_has_custom_permission(user: discord.Member, channel: discord.TextChannel, config: Dict) -> bool`: 檢查是否有自訂頻道權限
  - `_has_server_level_permission(user: discord.Member, config: Dict) -> bool`: 檢查是否有伺服器級別的自訂權限
  - `_get_all_channels(guild: discord.Guild) -> List[str]`: 取得伺服器所有文字頻道 ID
  - `_get_custom_permissions(user: discord.Member, config: Dict) -> Dict`: 取得自訂權限設定

## Functions

No top-level functions defined.
