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
  - `api_key` (`Any`): Instance attribute for api_key.
  - `_session` (`Optional[...]`): Instance attribute for _session.

- **Methods**:
  - `__init__(api_key) -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `_get_session() -> aiohttp.ClientSession`: Handles the `_get_session` functionality. Internally, it interacts with methods like `ClientSession`.
  - `close() -> Any`: 關閉 aiohttp session，應在 cog_unload 中呼叫。
  - `search(keyword, lang) -> list[...]`: 搜尋餐廳，返回最多 10 筆 PlaceResult 字典列表。
  - `_text_search(keyword) -> list[...]`: 呼叫 Foursquare Place Search API。
  - `_get_first_photo(fsq_id) -> str`: 取得餐廳第一張照片 URL。
  - `_to_place_result(place, photo_url) -> dict`: 將 Foursquare API 回應轉換為 PlaceResult 格式字典。
