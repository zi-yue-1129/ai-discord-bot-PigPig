# File: `addons/update/notifier.py`

## Overview
Discord 通知系統模組

## Classes

### `DiscordNotifier`
Discord 通知系統

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot) -> Any`: 初始化通知系統
  - `_get_bot_owner_safely() -> Optional[discord.User]`: 安全地獲取 Bot 擁有者
  - `notify_update_available(version_info: Dict[Tuple[str, Any]]) -> bool`: 通知有新版本可用
  - `notify_update_progress(stage: str, progress: int, details: str) -> bool`: 通知更新進度
  - `notify_update_complete(result: Dict[Tuple[str, Any]]) -> bool`: 通知更新完成
  - `notify_update_error(error: Exception, context: str) -> bool`: 通知更新錯誤
  - `notify_restart_success(restart_info: Dict[Tuple[str, Any]]) -> bool`: 通知重啟成功
  - `_create_progress_bar(progress: int, length: int) -> str`: 創建進度條
  - `send_channel_notification(channel_id: int, embed: discord.Embed) -> bool`: 發送頻道通知

### `QuickUpdateView`
快速更新視圖

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__() -> Any`: No description provided.
  - `quick_update(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 快速更新按鈕
  - `remind_later(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 稍後提醒按鈕
  - `ignore_update(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 忽略更新按鈕

## Functions

No module-level functions defined in this file.

