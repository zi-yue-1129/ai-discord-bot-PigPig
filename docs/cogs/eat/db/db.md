# File: `cogs/eat/db/db.py`

## Overview
Core file handling responsibilities within the `cogs/eat/db` subsystem.

## Classes

### `DB`
No description provided.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__() -> None`: No description provided.
  - `getKeywords() -> list`: No description provided.
  - `checkKeyword(keyword: String) -> Any`: No description provided.
  - `storeKeyword(keyword: str) -> None`: No description provided.
  - `storeSearchRecord(discord_id: str, title: str, keyword: str, map_rate: str, tag: str, map_address: str) -> int`: No description provided.
  - `getSearchRecoreds(discord_id: str) -> list`: No description provided.
  - `updateRecordRate(id: int, new_rate: float) -> bool`: No description provided.
  - `getRecentRecords(discord_id: str, days: int) -> list`: 取得最近 N 天內的搜尋記錄，用於避免重複推薦
  - `getLikedRecords(discord_id: str) -> list`: 取得 self_rate >= 1 的記錄（用戶喜歡的）
  - `getDislikedRecords(discord_id: str) -> list`: 取得 self_rate <= -1 的記錄（用戶不喜歡的）

## Functions

No module-level functions defined in this file.
