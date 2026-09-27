# File: `addons/update/downloader.py`

## Overview
更新下載管理器模組

負責安全地下載更新檔案，包括進度追蹤、檔案驗證和錯誤處理。

## Classes

### `UpdateDownloader`
更新下載管理器

- **Attributes**:
  - `download_dir` (`Any`): Instance attribute for download_dir.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(download_dir) -> Any`: 初始化下載管理器
  - `download_update(download_url, progress_callback, chunk_size) -> str`: 下載更新檔案
  - `_verify_download(filepath, expected_size) -> bool`: 驗證下載的檔案
  - `calculate_file_hash(filepath, algorithm) -> str`: 計算檔案雜湊值
  - `cleanup_downloads(keep_latest) -> None`: 清理下載目錄中的舊檔案
  - `get_download_dir() -> str`: 獲取下載目錄路徑
