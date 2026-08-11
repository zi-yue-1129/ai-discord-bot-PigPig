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
  - `_crawler` (`Any`): Instance attribute managing _crawler.

- **Methods**:
  - `async_search_list(keyword, lang) -> list[dict]`: Executes async_search_list operation.
  - `async_fetch_detail(url, lang) -> dict`: Executes async_fetch_detail operation.
  - `search(keyword, lang) -> list[dict]`: Executes search operation.
  - `close() -> Any`: Executes close operation.

## Functions

### `get_restaurant_provider() -> Any`
返回最合適的餐廳搜尋 Provider 實例。
