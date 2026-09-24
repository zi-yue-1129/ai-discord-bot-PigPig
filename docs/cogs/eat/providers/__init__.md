# File: `cogs/eat/providers/__init__.py`

## Overview
餐廳搜尋 Provider 工廠

## Classes

### `_SeleniumFallbackProvider`
將 GoogleMapCrawler 包裝為符合 Provider 介面的 fallback。

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(crawler) -> Any`: No description provided.
  - `async_search_list(keyword: str, lang: str) -> list[dict]`: No description provided.
  - `async_fetch_detail(url: str, lang: str) -> dict`: No description provided.
  - `search(keyword: str, lang: str) -> list[dict]`: No description provided.
  - `close() -> Any`: No description provided.

## Functions

### `get_restaurant_provider() -> Any`
返回最合適的餐廳搜尋 Provider 實例。
