# File: `cogs/eat/providers/googlemap_crawler.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `googlemap_crawler` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `GoogleMapCrawler`
Represents the `GoogleMapCrawler` class in the system.

- **Attributes**:
  - `_lock` (`Any`): Instance attribute for _lock.

- **Methods**:
  - `__init__() -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `Options` and `add_argument`.
  - `search_list(keyword, lang) -> list[...]`: 快速爬取搜尋結果列表。
  - `fetch_detail(url, lang) -> dict`: 導航至特定餐廳頁面，抓取詳盡資訊（地址、評分、照片等）。
  - `async_search_list(keyword, lang) -> list[...]`: Handles the `async_search_list` functionality. Internally, it interacts with methods like `get_running_loop` and `run_in_executor`.
  - `async_fetch_detail(url, lang) -> dict`: Handles the `async_fetch_detail` functionality. Internally, it interacts with methods like `get_running_loop` and `run_in_executor`.
  - `close() -> Any`: Handles the `close` functionality. Internally, it interacts with methods like `acquire` and `quit`.
