# File: `llm/utils/file_watcher.py`

## Overview
The `FileWatcher` class provides file monitoring and hot-reload functionality for the LLM system. It enables automatic detection of configuration file changes and triggers appropriate reload mechanisms.

## Classes

### `FileWatcher`
檔案監控和熱重載

- **Attributes**:
  - `check_interval` (`Any`): Instance attribute managing check_interval.
  - `_running` (`Any`): Instance attribute managing _running.
  - `_thread` (`Any`): Instance attribute managing _thread.
  - `_lock` (`Any`): Instance attribute managing _lock.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `watch_file(path, callback) -> Any`: 監控檔案變更  Args:     path: 要監控的檔案路徑     callback: 檔案變更時的回調函式
  - `stop_watching() -> Any`: 停止監控
  - `check_changes() -> bool`: 手動檢查變更  Returns:     bool: 是否檢測到變更
  - `add_file(path, callback) -> Any`: 添加要監控的檔案（watch_file 的別名）  Args:     path: 檔案路徑     callback: 回調函式
  - `remove_file(path) -> Any`: 移除監控檔案  Args:     path: 要移除的檔案路徑
  - `get_watched_files() -> Set[str]`: 獲取正在監控的檔案列表  Returns:     正在監控的檔案路徑集合
  - `is_watching(path) -> bool`: 檢查是否正在監控指定檔案  Args:     path: 檔案路徑      Returns:     bool: 是否正在監控
  - `get_file_info(path) -> Dict[Tuple[str, Any]]`: 獲取監控檔案的資訊  Args:     path: 檔案路徑      Returns:     檔案資訊字典
  - `get_watcher_stats() -> Dict[Tuple[str, Any]]`: 獲取監控器統計資訊  Returns:     統計資訊字典

