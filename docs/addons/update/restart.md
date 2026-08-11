# File: `addons/update/restart.py`

## Overview
簡單可靠的重啟管理模組

採用直接、簡單但可靠的重啟機制，放棄複雜的進程分離方案。
使用系統級重啟命令和強制退出機制確保重啟成功。

## Classes

### `SimpleRestartManager`
簡單可靠的重啟管理器

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `logger` (`Any`): Instance attribute managing logger.
  - `restart_config` (`Any`): Instance attribute managing restart_config.

- **Methods**:
  - `execute_restart(reason) -> None`: 執行簡單重啟流程  Args:     reason: 重啟原因
  - `post_restart_check() -> bool`: 重啟後檢查  Returns:     檢查是否通過
  - `is_restart_pending() -> bool`: 檢查是否有待處理的重啟
  - `get_restart_info() -> Optional[Dict[Tuple[str, Any]]]`: 獲取重啟資訊
  - `cancel_restart() -> bool`: 取消重啟

