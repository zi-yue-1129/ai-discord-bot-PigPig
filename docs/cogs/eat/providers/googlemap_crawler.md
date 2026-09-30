# File: `cogs/eat/providers/googlemap_crawler.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/eat/providers/googlemap_crawler.py`.

## Classes

### `GoogleMapCrawler`
Class representing GoogleMapCrawler.

- **Attributes**:
  - `_lock` (`Any`): Instance attribute _lock
  - `webdriver` (`Any`): Instance attribute webdriver

- **Methods**:
  - `search_list(self, keyword, lang) -> list[dict]`: 快速爬取搜尋結果列表。  Returns:     list[dict]: 包含 name, maps_url 的初步字典列表。
  - `fetch_detail(self, url, lang) -> dict`: 導航至特定餐廳頁面，抓取詳盡資訊（地址、評分、照片等）。
  - `async_search_list(self, keyword, lang) -> list[dict]`: Method async_search_list.
  - `async_fetch_detail(self, url, lang) -> dict`: Method async_fetch_detail.
  - `close(self) -> Any`: Method close.

## Functions

None
