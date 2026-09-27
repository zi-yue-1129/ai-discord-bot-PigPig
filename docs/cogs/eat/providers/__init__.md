# File: `cogs/eat/providers/__init__.py`

## Overview
餐廳搜尋 Provider 工廠

根據環境變數自動選擇最合適的 Provider：
- 有 FOURSQUARE_API_KEY → FoursquareProvider（免費 API，每月 1000 次）
- 否則 → GoogleMapCrawler fallback（Selenium 爬蟲，較慢但無費用限制）

## Classes

### `_SeleniumFallbackProvider`
將 GoogleMapCrawler 包裝為符合 Provider 介面的 fallback。

- **Attributes**:
  - `_crawler` (`Any`): Instance attribute for _crawler.

- **Methods**:
  - `__init__(crawler) -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `async_search_list(keyword, lang) -> list[...]`: Handles the `async_search_list` functionality. Internally, it interacts with methods like `async_search_list`.
  - `async_fetch_detail(url, lang) -> dict`: Handles the `async_fetch_detail` functionality. Internally, it interacts with methods like `async_fetch_detail`.
  - `search(keyword, lang) -> list[...]`: Handles the `search` functionality. Internally, it interacts with methods like `async_search_list`.
  - `close() -> Any`: Handles the `close` functionality. Internally, it interacts with methods like `close`.

## Functions

### `get_restaurant_provider() -> Any`
返回最合適的餐廳搜尋 Provider 實例。
