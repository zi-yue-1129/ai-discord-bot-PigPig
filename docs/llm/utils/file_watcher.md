# File: `llm/utils/file_watcher.py`

## Overview
The `FileWatcher` class provides file monitoring and hot-reload functionality for the LLM system. It enables automatic detection of configuration file changes and triggers appropriate reload mechanisms.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `file_watcher.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `FileWatcher`
檔案監控和熱重載

- **Attributes**:
  - `check_interval` (`Any`): Internal instance state.
  - `_running` (`Any`): Internal instance state.
  - `_thread` (`Any`): Internal instance state.
  - `_lock` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

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
  - `get_file_info(path: str) -> Dict[Tuple]`: 獲取監控檔案的資訊
  - `get_watcher_stats() -> Dict[Tuple]`: 獲取監控器統計資訊
