# File: `cogs/eat/providers/foursquare_provider.py`

## Overview
Foursquare Places API v3 Provider

免費層：每月 1000 次 API 呼叫
API 文件：https://docs.foursquare.com/developer/reference/place-search

## Classes

### `FoursquareProvider`
Foursquare Places API 非同步 Provider。

使用 aiohttp 發送非阻塞 HTTP 請求，取得餐廳列表和詳細資訊。
無 API key 時請改用 GoogleMapCrawler fallback。

- **Attributes**:
  - `api_key` (`Any`): Instance attribute managing api_key.

- **Methods**:
  - `close() -> Any`: 關閉 aiohttp session，應在 cog_unload 中呼叫。
  - `search(keyword, lang) -> list[dict]`: 搜尋餐廳，返回最多 10 筆 PlaceResult 字典列表。  Args:     keyword: 搜尋關鍵字（例如：「日本料理」、「牛肉麵」）  Returns:     list[dict]：PlaceResult 相容字典列表，失敗時返回空列表
