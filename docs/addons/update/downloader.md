# File: `addons/update/downloader.py`

## Overview
更新下載管理器模組

負責安全地下載更新檔案，包括進度追蹤、檔案驗證和錯誤處理。

## Classes

### `UpdateDownloader`
更新下載管理器

- **Attributes**:
  - `download_dir` (`Any`): Instance attribute download_dir
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `download_update(self, download_url, progress_callback, chunk_size) -> str`: 下載更新檔案  Args:     download_url: 下載連結     progress_callback: 進度回調函數     chunk_size: 下載塊大小      Returns:     下載的檔案路徑      Raises:     Exception: 下載過程中的各種錯誤
  - `_verify_download(self, filepath, expected_size) -> bool`: 驗證下載的檔案  Args:     filepath: 檔案路徑     expected_size: 預期檔案大小      Returns:     驗證是否通過
  - `calculate_file_hash(self, filepath, algorithm) -> str`: 計算檔案雜湊值  Args:     filepath: 檔案路徑     algorithm: 雜湊演算法      Returns:     檔案雜湊值
  - `cleanup_downloads(self, keep_latest) -> None`: 清理下載目錄中的舊檔案  Args:     keep_latest: 保留最新的檔案數量
  - `get_download_dir(self) -> str`: 獲取下載目錄路徑  Returns:     下載目錄路徑

## Functions

None

