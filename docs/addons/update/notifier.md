# File: `addons/update/notifier.py`

## Overview
This file belongs to the Addons Subsystem. Its core responsibility is to handle logic related to `notifier.py`, providing vital integrations within the PigPig bot ecosystem.
Discord 通知系統模組

負責發送更新相關的通知給 Bot 擁有者和管理員。

## Classes

### `DiscordNotifier`
Discord 通知系統

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.
  - `owner_id` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any) -> Any`: 初始化通知系統
  - `_get_bot_owner_safely() -> Optional[discord.User]`: 安全地獲取 Bot 擁有者
  - `notify_update_available(version_info: Dict[Tuple]) -> bool`: 通知有新版本可用
  - `notify_update_progress(stage: str, progress: int, details: str) -> bool`: 通知更新進度
  - `notify_update_complete(result: Dict[Tuple]) -> bool`: 通知更新完成
  - `notify_update_error(error: Exception, context: str) -> bool`: 通知更新錯誤
  - `notify_restart_success(restart_info: Dict[Tuple]) -> bool`: 通知重啟成功
  - `_create_progress_bar(progress: int, length: int) -> str`: 創建進度條
  - `send_channel_notification(channel_id: int, embed: discord.Embed) -> bool`: 發送頻道通知

### `QuickUpdateView`
快速更新視圖

- **Methods**:
  - `__init__() -> Any`: Performs internal processing logic.
  - `quick_update(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 快速更新按鈕
  - `remind_later(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 稍後提醒按鈕
  - `ignore_update(interaction: discord.Interaction, button: discord.ui.Button) -> Any`: 忽略更新按鈕


## Handwritten Context
# Notifier Module

**File:** [`addons/update/notifier.py`](addons/update/notifier.py)

This module is responsible for sending notifications related to the update process via Discord. It primarily communicates with the bot owner through DMs.

## `DiscordNotifier` Class

This class handles the sending of various notifications.

### `__init__(self, bot)`

Initializes the notifier.

*   **Parameters:**
    *   `bot`: The instance of the Discord bot.

### Methods

#### `async notify_update_available(self, version_info: Dict[str, Any]) -> bool`

Sends a notification that a new version is available, including release notes and an option to start the update.

*   **Parameters:**
    *   `version_info` (Dict[str, Any]): A dictionary containing details about the new version.
*   **Returns:** `True` if the notification was sent successfully, `False` otherwise.

#### `async notify_update_progress(self, stage: str, progress: int, details: str = "") -> bool`

Sends a notification about the current progress of an ongoing update.

*   **Parameters:**
    *   `stage` (str): The current stage of the update (e.g., "downloading", "installing").
    *   `progress` (int): The progress percentage (0-100).
    *   `details` (str): Optional additional details about the current step.
*   **Returns:** `True` if the notification was sent successfully.

#### `async notify_update_complete(self, result: Dict[str, Any]) -> bool`

Sends a notification when the update process is complete, indicating success or failure.

*   **Parameters:**
    *   `result` (Dict[str, Any]): A dictionary containing the results of the update.
*   **Returns:** `True` if the notification was sent successfully.

#### `async notify_update_error(self, error: Exception, context: str = "") -> bool`

Sends a notification when an error occurs during the update process.

*   **Parameters:**
    *   `error` (Exception): The exception object that was raised.
    *   `context` (str): The context in which the error occurred.
*   **Returns:** `True` if the notification was sent successfully.

#### `async notify_restart_success(self, restart_info: Dict[str, Any]) -> bool`

Sends a notification after the bot has successfully restarted.

*   **Parameters:**
    *   `restart_info` (Dict[str, Any]): Information about the restart.
*   **Returns:** `True` if the notification was sent successfully.

## `QuickUpdateView` Class

This `discord.ui.View` provides buttons for the user to interact with an update notification.

### Buttons

*   **Update Now:** Starts the update process. Can only be used by the bot owner.
*   **Remind Later:** Dismisses the current notification, which will reappear at the next update check.
*   **Ignore:** Ignores the current update notification.