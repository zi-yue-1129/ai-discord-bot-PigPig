# File: `addons/update/restart.py`

## Overview
簡單可靠的重啟管理模組

## Classes

### `SimpleRestartManager`
簡單可靠的重啟管理器

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot, restart_config: Optional[Dict[Tuple[str, Any]]]) -> Any`: 初始化重啟管理器
  - `execute_restart(reason: str) -> None`: 執行簡單重啟流程
  - `post_restart_check() -> bool`: 重啟後檢查
  - `_save_restart_flag(reason: str) -> None`: 保存重啟標記
  - `_notify_restart() -> None`: 通知即將重啟
  - `_shutdown_bot() -> None`: 關閉 Bot
  - `_execute_simple_restart() -> None`: 執行簡單重啟
  - `_windows_simple_restart(python_exe: str, current_dir: str) -> bool`: Windows 簡單重啟方法
  - `_unix_simple_restart(python_exe: str, current_dir: str) -> bool`: Unix/Linux 簡單重啟方法
  - `_simple_health_check() -> bool`: 簡單健康檢查
  - `_notify_restart_success(restart_info: Dict[Tuple[str, Any]]) -> None`: 通知重啟成功
  - `_notify_restart_failure(error: Exception) -> None`: 通知重啟失敗
  - `_handle_restart_failure(error: Exception) -> None`: 處理重啟失敗
  - `_create_emergency_restart_file() -> None`: 創建緊急重啟指示文件
  - `is_restart_pending() -> bool`: 檢查是否有待處理的重啟
  - `get_restart_info() -> Optional[Dict[Tuple[str, Any]]]`: 獲取重啟資訊
  - `cancel_restart() -> bool`: 取消重啟

## Functions

No module-level functions defined in this file.

