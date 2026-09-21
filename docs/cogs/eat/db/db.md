# File: `cogs/eat/db/db.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `DB`
Core class implementation.

- **Attributes**:
  - `engine` (`Any`): Attribute holding engine data.

- **Methods**:
  - `__init__() -> None`: Executes __init__ logic.
  - `getKeywords() -> list`: Executes getKeywords logic.
  - `checkKeyword(keyword: String) -> Any`: Executes checkKeyword logic.
  - `storeKeyword(keyword: str) -> None`: Executes storeKeyword logic.
  - `storeSearchRecord(discord_id: str, title: str, keyword: str, map_rate: str, tag: str, map_address: str) -> int`: Executes storeSearchRecord logic.
  - `getSearchRecoreds(discord_id: str) -> list`: Executes getSearchRecoreds logic.
  - `updateRecordRate(id: int, new_rate: float) -> bool`: Executes updateRecordRate logic.
  - `getRecentRecords(discord_id: str, days: int) -> list`: 取得最近 N 天內的搜尋記錄，用於避免重複推薦
  - `getLikedRecords(discord_id: str) -> list`: 取得 self_rate >= 1 的記錄（用戶喜歡的）
  - `getDislikedRecords(discord_id: str) -> list`: 取得 self_rate <= -1 的記錄（用戶不喜歡的）

## Functions

No top-level functions defined.
