# File: `addons/update/notifier.py`

## Overview
Discord 通知系統模組

負責發送更新相關的通知給 Bot 擁有者和管理員。

## Classes

### `DiscordNotifier`
Discord 通知系統

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `logger` (`Any`): Instance attribute managing logger.
  - `owner_id` (`Any`): Instance attribute managing owner_id.

- **Methods**:
  - `notify_update_available(version_info) -> bool`: 通知有新版本可用  Args:     version_info: 版本資訊字典      Returns:     通知是否發送成功
  - `notify_update_progress(stage, progress, details) -> bool`: 通知更新進度  Args:     stage: 當前階段     progress: 進度百分比     details: 詳細資訊      Returns:     通知是否發送成功
  - `notify_update_complete(result) -> bool`: 通知更新完成  Args:     result: 更新結果字典      Returns:     通知是否發送成功
  - `notify_update_error(error, context) -> bool`: 通知更新錯誤  Args:     error: 錯誤物件     context: 錯誤上下文      Returns:     通知是否發送成功
  - `notify_restart_success(restart_info) -> bool`: 通知重啟成功  Args:     restart_info: 重啟資訊      Returns:     通知是否發送成功
  - `send_channel_notification(channel_id, embed) -> bool`: 發送頻道通知  Args:     channel_id: 頻道 ID     embed: 嵌入訊息      Returns:     通知是否發送成功

### `QuickUpdateView`
快速更新視圖

- **Methods**:
  - `quick_update(interaction, button) -> Any`: 快速更新按鈕
  - `remind_later(interaction, button) -> Any`: 稍後提醒按鈕
  - `ignore_update(interaction, button) -> Any`: 忽略更新按鈕

