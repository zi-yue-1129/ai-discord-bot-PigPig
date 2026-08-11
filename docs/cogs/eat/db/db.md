# File: `cogs/eat/db/db.py`

## Overview
Core logic and functionalities for db.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Classes

### `DB`
Represents DB.

- **Attributes**:
  - `engine` (`Any`): Instance attribute managing engine.

- **Methods**:
  - `getKeywords() -> list`: Executes getKeywords operation.
  - `checkKeyword(keyword) -> Any`: Executes checkKeyword operation.
  - `storeKeyword(keyword) -> None`: Executes storeKeyword operation.
  - `storeSearchRecord(discord_id, title, keyword, map_rate, tag, map_address) -> int`: Executes storeSearchRecord operation.
  - `getSearchRecoreds(discord_id) -> list`: Executes getSearchRecoreds operation.
  - `updateRecordRate(id, new_rate) -> bool`: Executes updateRecordRate operation.
  - `getRecentRecords(discord_id, days) -> list`: 取得最近 N 天內的搜尋記錄，用於避免重複推薦
  - `getLikedRecords(discord_id) -> list`: 取得 self_rate >= 1 的記錄（用戶喜歡的）
  - `getDislikedRecords(discord_id) -> list`: 取得 self_rate <= -1 的記錄（用戶不喜歡的）
