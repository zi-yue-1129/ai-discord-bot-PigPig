# File: `addons/update/restart.py`

## Overview
簡單可靠的重啟管理模組

採用直接、簡單但可靠的重啟機制，放棄複雜的進程分離方案。
使用系統級重啟命令和強制退出機制確保重啟成功。

## Classes

### `SimpleRestartManager`
簡單可靠的重啟管理器

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `logger` (`Any`): Instance attribute for logger.
  - `restart_config` (`Any`): Instance attribute for restart_config.

- **Methods**:
  - `__init__(bot, restart_config) -> Any`: 初始化重啟管理器
  - `execute_restart(reason) -> None`: 執行簡單重啟流程
  - `post_restart_check() -> bool`: 重啟後檢查
  - `_save_restart_flag(reason) -> None`: 保存重啟標記
  - `_notify_restart() -> None`: 通知即將重啟
  - `_shutdown_bot() -> None`: 關閉 Bot
  - `_execute_simple_restart() -> None`: 執行簡單重啟
  - `_windows_simple_restart(python_exe, current_dir) -> bool`: Windows 簡單重啟方法
  - `_unix_simple_restart(python_exe, current_dir) -> bool`: Unix/Linux 簡單重啟方法
  - `_simple_health_check() -> bool`: 簡單健康檢查
  - `_notify_restart_success(restart_info) -> None`: 通知重啟成功
  - `_notify_restart_failure(error) -> None`: 通知重啟失敗
  - `_handle_restart_failure(error) -> None`: 處理重啟失敗
  - `_create_emergency_restart_file() -> None`: 創建緊急重啟指示文件
  - `is_restart_pending() -> bool`: 檢查是否有待處理的重啟
  - `get_restart_info() -> Optional[...]`: 獲取重啟資訊
  - `cancel_restart() -> bool`: 取消重啟
