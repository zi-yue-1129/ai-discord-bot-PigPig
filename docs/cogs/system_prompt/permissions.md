# File: `cogs/system_prompt/permissions.py`

## Overview
This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `permissions.py`, providing vital integrations within the PigPig bot ecosystem.
頻道系統提示管理模組的權限驗證器

提供完整的權限檢查和驗證邏輯，支援多層權限控制。

## Classes

### `PermissionValidator`
權限驗證器類別

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: discord.Client) -> Any`: 初始化權限驗證器
  - `can_modify_channel_prompt(user: discord.Member, channel: discord.TextChannel, config: Optional[Dict]) -> bool`: 檢查用戶是否可修改頻道提示
  - `can_modify_server_prompt(user: discord.Member, guild: discord.Guild, config: Optional[Dict]) -> bool`: 檢查用戶是否可修改伺服器提示
  - `can_view_prompt(user: discord.Member, channel: Optional[discord.TextChannel]) -> bool`: 檢查用戶是否可查看系統提示
  - `get_user_permissions(user: discord.Member, guild: discord.Guild, config: Optional[Dict]) -> Dict[Tuple]`: 取得用戶的詳細權限資訊
  - `validate_permission_or_raise(user: discord.Member, action: str, target: any, config: Optional[Dict]) -> None`: 驗證權限，如果沒有權限則拋出例外
  - `_is_bot_owner(user: discord.Member) -> bool`: 檢查是否為機器人擁有者
  - `_has_custom_permission(user: discord.Member, channel: discord.TextChannel, config: Dict) -> bool`: 檢查是否有自訂頻道權限
  - `_has_server_level_permission(user: discord.Member, config: Dict) -> bool`: 檢查是否有伺服器級別的自訂權限
  - `_get_all_channels(guild: discord.Guild) -> List[str]`: 取得伺服器所有文字頻道 ID
  - `_get_custom_permissions(user: discord.Member, config: Dict) -> Dict`: 取得自訂權限設定


## Handwritten Context
# System Prompt System - Permissions

**File:** [`cogs/system_prompt/permissions.py`](cogs/system_prompt/permissions.py)

The `PermissionValidator` class is the dedicated security component for the system prompt feature. It provides a centralized place to check if a user has the authority to perform specific actions, such as viewing, editing, or removing prompts.

## `PermissionValidator` Class

### `__init__(self, bot)`

Initializes the validator with a reference to the bot instance, which is needed to fetch user and guild information.

### Key Methods

#### `can_modify_channel_prompt(self, user, channel, ...)`

Checks if a user has permission to modify the system prompt for a specific channel.

*   **Permission Hierarchy (in order):**
    1.  **Bot Owner:** Always has permission.
    2.  **Server Administrator:** Users with the `Administrator` permission in the server.
    3.  **Channel Manager:** Users with the `Manage Channels` permission for that specific channel.
    4.  **Custom Permissions:** Checks the server's configuration file for any custom roles or users that have been granted permission.

#### `can_modify_server_prompt(self, user, guild, ...)`

Checks if a user has permission to modify the server-wide default system prompt.

*   **Permission Hierarchy:**
    1.  **Bot Owner:** Always has permission.
    2.  **Server Administrator:** Users with the `Administrator` permission.
    3.  **Custom Permissions:** Checks the server's configuration for roles that have been granted server-level prompt management permissions.

#### `can_view_prompt(self, user, channel, ...)`

Checks if a user can view a prompt. This permission is intentionally broad: any user who can view a channel is allowed to see the system prompt that applies to it.

#### `validate_permission_or_raise(self, user, action, ...)`

A crucial enforcement method used by the command handlers. It performs a permission check and, if the check fails, it raises a `PermissionError`. This simplifies the code in the command handlers, as they can wrap their logic in a `try...except` block.