# File: `addons/update/notifier.py`

## Overview
Discord 通知系統模組

負責發送更新相關的通知給 Bot 擁有者和管理員。

## Classes

### `DiscordNotifier`
Discord 通知系統

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `logger` (`Any`): Instance attribute logger
  - `owner_id` (`Any`): Instance attribute owner_id

- **Methods**:
  - `_get_bot_owner_safely(self) -> Optional[discord.User]`: 安全地獲取 Bot 擁有者  Returns:     Bot 擁有者物件，如果獲取失敗則返回 None
  - `notify_update_available(self, version_info) -> bool`: 通知有新版本可用  Args:     version_info: 版本資訊字典      Returns:     通知是否發送成功
  - `notify_update_progress(self, stage, progress, details) -> bool`: 通知更新進度  Args:     stage: 當前階段     progress: 進度百分比     details: 詳細資訊      Returns:     通知是否發送成功
  - `notify_update_complete(self, result) -> bool`: 通知更新完成  Args:     result: 更新結果字典      Returns:     通知是否發送成功
  - `notify_update_error(self, error, context) -> bool`: 通知更新錯誤  Args:     error: 錯誤物件     context: 錯誤上下文      Returns:     通知是否發送成功
  - `notify_restart_success(self, restart_info) -> bool`: 通知重啟成功  Args:     restart_info: 重啟資訊      Returns:     通知是否發送成功
  - `_create_progress_bar(self, progress, length) -> str`: 創建進度條  Args:     progress: 進度百分比 (0-100)     length: 進度條長度      Returns:     進度條字串
  - `send_channel_notification(self, channel_id, embed) -> bool`: 發送頻道通知  Args:     channel_id: 頻道 ID     embed: 嵌入訊息      Returns:     通知是否發送成功

### `QuickUpdateView`
快速更新視圖

- **Attributes**:
  - None

- **Methods**:
  - `quick_update(self, interaction, button) -> Any`: 快速更新按鈕
  - `remind_later(self, interaction, button) -> Any`: 稍後提醒按鈕
  - `ignore_update(self, interaction, button) -> Any`: 忽略更新按鈕

## Functions

None

