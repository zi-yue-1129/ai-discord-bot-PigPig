# File: `llm/utils/file_watcher.py`

## Overview
Core file handling responsibilities within the `llm/utils` subsystem.

## Classes

### `FileWatcher`
檔案監控和熱重載

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(check_interval: float) -> Any`: 初始化檔案監控器
  - `watch_file(path: str, callback: Callable) -> Any`: 監控檔案變更
  - `_start_watching() -> Any`: 開始監控執行緒
  - `_watch_loop() -> Any`: 監控迴圈
  - `stop_watching() -> Any`: 停止監控
  - `check_changes() -> bool`: 手動檢查變更
  - `add_file(path: str, callback: Callable) -> Any`: 添加要監控的檔案（watch_file 的別名）
  - `remove_file(path: str) -> Any`: 移除監控檔案
  - `get_watched_files() -> Set[str]`: 獲取正在監控的檔案列表
  - `is_watching(path: str) -> bool`: 檢查是否正在監控指定檔案
  - `get_file_info(path: str) -> Dict[Tuple[str, Any]]`: 獲取監控檔案的資訊
  - `get_watcher_stats() -> Dict[Tuple[str, Any]]`: 獲取監控器統計資訊

## Functions

No module-level functions defined in this file.

