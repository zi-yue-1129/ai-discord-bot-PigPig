# File: `cogs/eat/providers/googlemap_crawler.py`

## Overview
Core file handling responsibilities within the `cogs/eat/providers` subsystem.

## Classes

### `GoogleMapCrawler`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__() -> Any`: No description provided.
  - `search_list(keyword: str, lang: str) -> list[dict]`: 快速爬取搜尋結果列表。
  - `fetch_detail(url: str, lang: str) -> dict`: 導航至特定餐廳頁面，抓取詳盡資訊（地址、評分、照片等）。
  - `async_search_list(keyword: str, lang: str) -> list[dict]`: No description provided.
  - `async_fetch_detail(url: str, lang: str) -> dict`: No description provided.
  - `close() -> Any`: No description provided.

## Functions

No module-level functions defined in this file.
