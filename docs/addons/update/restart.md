# File: `addons/update/restart.py`

## Overview
This file belongs to the Addons Subsystem. Its core responsibility is to handle logic related to `restart.py`, providing vital integrations within the PigPig bot ecosystem.
簡單可靠的重啟管理模組

採用直接、簡單但可靠的重啟機制，放棄複雜的進程分離方案。
使用系統級重啟命令和強制退出機制確保重啟成功。

## Classes

### `SimpleRestartManager`
簡單可靠的重啟管理器

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.
  - `restart_config` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any, restart_config: Optional[Dict[Tuple]]) -> Any`: 初始化重啟管理器
  - `execute_restart(reason: str) -> None`: 執行簡單重啟流程
  - `post_restart_check() -> bool`: 重啟後檢查
  - `_save_restart_flag(reason: str) -> None`: 保存重啟標記
  - `_notify_restart() -> None`: 通知即將重啟
  - `_shutdown_bot() -> None`: 關閉 Bot
  - `_execute_simple_restart() -> None`: 執行簡單重啟
  - `_windows_simple_restart(python_exe: str, current_dir: str) -> bool`: Windows 簡單重啟方法
  - `_unix_simple_restart(python_exe: str, current_dir: str) -> bool`: Unix/Linux 簡單重啟方法
  - `_simple_health_check() -> bool`: 簡單健康檢查
  - `_notify_restart_success(restart_info: Dict[Tuple]) -> None`: 通知重啟成功
  - `_notify_restart_failure(error: Exception) -> None`: 通知重啟失敗
  - `_handle_restart_failure(error: Exception) -> None`: 處理重啟失敗
  - `_create_emergency_restart_file() -> None`: 創建緊急重啟指示文件
  - `is_restart_pending() -> bool`: 檢查是否有待處理的重啟
  - `get_restart_info() -> Optional[Dict[Tuple]]`: 獲取重啟資訊
  - `cancel_restart() -> bool`: 取消重啟


## Handwritten Context
# Restart Module

**File:** [`addons/update/restart.py`](addons/update/restart.py)

This module provides a simple and reliable mechanism for restarting the bot, which is crucial after an update. It is designed to be robust, using system-level commands to ensure the restart process completes successfully.

## `SimpleRestartManager` Class

This class (also aliased as `GracefulRestartManager`) manages the entire restart process.

### `__init__(self, bot, restart_config: Optional[Dict[str, Any]] = None)`

Initializes the restart manager.

*   **Parameters:**
    *   `bot`: The instance of the Discord bot.
    *   `restart_config` (Optional[Dict[str, Any]]): A dictionary containing restart configuration, such as the path for the restart flag file and delay settings.

### Methods

#### `async execute_restart(self, reason: str = "update_restart") -> None`

Executes the restart process. This involves saving a restart flag, shutting down the bot gracefully, and then executing a system-specific command to start the bot again.

*   **Parameters:**
    *   `reason` (str): The reason for the restart, which is logged.

#### `async post_restart_check(self) -> bool`

Performs a check after the bot has restarted. It looks for the restart flag file to confirm that the restart was intentional and then runs a simple health check.

*   **Returns:** `True` if the check passes or if it was a normal startup, `False` if the health check fails.

#### `is_restart_pending(self) -> bool`

Checks if a restart is pending by looking for the existence of the restart flag file.

*   **Returns:** `True` if a restart is pending, `False` otherwise.

#### `cancel_restart(self) -> bool`

Cancels a pending restart by deleting the restart flag file.

*   **Returns:** `True` if the restart was successfully canceled, `False` otherwise.

### Example Usage

```python
# This class is typically used internally by the UpdateManager.
# The following is a conceptual example.

import asyncio
from addons.update.restart import SimpleRestartManager

# Assuming 'bot' is your discord.Client instance
# bot = discord.Client() 

async def perform_restart(bot_instance):
    restart_manager = SimpleRestartManager(bot_instance)
    
    print("Initiating restart...")
    await restart_manager.execute_restart(reason="manual_restart")
    print("This line will likely not be reached as the process exits.")

# To run this, you would need a running bot instance.
# asyncio.run(perform_restart(bot))