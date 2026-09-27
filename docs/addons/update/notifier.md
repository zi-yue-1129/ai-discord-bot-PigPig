# File: `addons/update/notifier.py`

## Overview
Discord 通知系統模組

負責發送更新相關的通知給 Bot 擁有者和管理員。

## Classes

### `DiscordNotifier`
Discord 通知系統

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `logger` (`Any`): Instance attribute for logger.
  - `owner_id` (`Any`): Instance attribute for owner_id.

- **Methods**:
  - `__init__(bot) -> Any`: 初始化通知系統
  - `_get_bot_owner_safely() -> Optional[...]`: 安全地獲取 Bot 擁有者
  - `notify_update_available(version_info) -> bool`: 通知有新版本可用
  - `notify_update_progress(stage, progress, details) -> bool`: 通知更新進度
  - `notify_update_complete(result) -> bool`: 通知更新完成
  - `notify_update_error(error, context) -> bool`: 通知更新錯誤
  - `notify_restart_success(restart_info) -> bool`: 通知重啟成功
  - `_create_progress_bar(progress, length) -> str`: 創建進度條
  - `send_channel_notification(channel_id, embed) -> bool`: 發送頻道通知

### `QuickUpdateView`
快速更新視圖

- **Methods**:
  - `__init__() -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `__init__`.
  - `quick_update(interaction, button) -> Any`: 快速更新按鈕
  - `remind_later(interaction, button) -> Any`: 稍後提醒按鈕
  - `ignore_update(interaction, button) -> Any`: 忽略更新按鈕
