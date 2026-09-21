# File: `cogs/eat/providers/googlemap_crawler.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `GoogleMapCrawler`
Core class implementation.

- **Attributes**:
  - `_lock` (`Any`): Attribute holding _lock data.

- **Methods**:
  - `__init__() -> Any`: Executes __init__ logic.
  - `search_list(keyword: str, lang: str) -> list[dict]`: 快速爬取搜尋結果列表。
  - `fetch_detail(url: str, lang: str) -> dict`: 導航至特定餐廳頁面，抓取詳盡資訊（地址、評分、照片等）。
  - `async_search_list(keyword: str, lang: str) -> list[dict]`: Executes async_search_list logic.
  - `async_fetch_detail(url: str, lang: str) -> dict`: Executes async_fetch_detail logic.
  - `close() -> Any`: Executes close logic.

## Functions

No top-level functions defined.
