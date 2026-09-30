# File: `llm/utils/file_watcher.py`

## Overview
This file is part of the LLM integration and orchestration pipeline and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `llm/utils/file_watcher.py`.

## Classes

### `FileWatcher`
檔案監控和熱重載

- **Attributes**:
  - `watched_files` (`Dict[str, datetime]`): Instance attribute watched_files
  - `callbacks` (`Dict[str, Callable]`): Instance attribute callbacks
  - `check_interval` (`Any`): Instance attribute check_interval
  - `_running` (`Any`): Instance attribute _running
  - `_thread` (`Any`): Instance attribute _thread
  - `_lock` (`Any`): Instance attribute _lock
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `watch_file(self, path, callback) -> Any`: 監控檔案變更  Args:     path: 要監控的檔案路徑     callback: 檔案變更時的回調函式
  - `_start_watching(self) -> Any`: 開始監控執行緒
  - `_watch_loop(self) -> Any`: 監控迴圈
  - `stop_watching(self) -> Any`: 停止監控
  - `check_changes(self) -> bool`: 手動檢查變更  Returns:     bool: 是否檢測到變更
  - `add_file(self, path, callback) -> Any`: 添加要監控的檔案（watch_file 的別名）  Args:     path: 檔案路徑     callback: 回調函式
  - `remove_file(self, path) -> Any`: 移除監控檔案  Args:     path: 要移除的檔案路徑
  - `get_watched_files(self) -> Set[str]`: 獲取正在監控的檔案列表  Returns:     正在監控的檔案路徑集合
  - `is_watching(self, path) -> bool`: 檢查是否正在監控指定檔案  Args:     path: 檔案路徑      Returns:     bool: 是否正在監控
  - `get_file_info(self, path) -> Dict[str, Any]`: 獲取監控檔案的資訊  Args:     path: 檔案路徑      Returns:     檔案資訊字典
  - `get_watcher_stats(self) -> Dict[str, Any]`: 獲取監控器統計資訊  Returns:     統計資訊字典

## Functions

None

