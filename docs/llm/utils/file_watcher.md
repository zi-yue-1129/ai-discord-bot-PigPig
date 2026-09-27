# File: `llm/utils/file_watcher.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `file_watcher` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `FileWatcher`
檔案監控和熱重載

- **Attributes**:
  - `watched_files` (`Dict[...]`): Instance attribute for watched_files.
  - `callbacks` (`Dict[...]`): Instance attribute for callbacks.
  - `check_interval` (`Any`): Instance attribute for check_interval.
  - `_running` (`Any`): Instance attribute for _running.
  - `_thread` (`Any`): Instance attribute for _thread.
  - `_lock` (`Any`): Instance attribute for _lock.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(check_interval) -> Any`: 初始化檔案監控器
  - `watch_file(path, callback) -> Any`: 監控檔案變更
  - `_start_watching() -> Any`: 開始監控執行緒
  - `_watch_loop() -> Any`: 監控迴圈
  - `stop_watching() -> Any`: 停止監控
  - `check_changes() -> bool`: 手動檢查變更
  - `add_file(path, callback) -> Any`: 添加要監控的檔案（watch_file 的別名）
  - `remove_file(path) -> Any`: 移除監控檔案
  - `get_watched_files() -> Set[...]`: 獲取正在監控的檔案列表
  - `is_watching(path) -> bool`: 檢查是否正在監控指定檔案
  - `get_file_info(path) -> Dict[...]`: 獲取監控檔案的資訊
  - `get_watcher_stats() -> Dict[...]`: 獲取監控器統計資訊
