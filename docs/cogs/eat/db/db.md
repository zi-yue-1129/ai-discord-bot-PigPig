# File: `cogs/eat/db/db.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/eat/db/db.py`.

## Classes

### `DB`
Class representing DB.

- **Attributes**:
  - `engine` (`Any`): Instance attribute engine

- **Methods**:
  - `getKeywords(self) -> list`: Method getKeywords.
  - `checkKeyword(self, keyword) -> Any`: Method checkKeyword.
  - `storeKeyword(self, keyword) -> None`: Method storeKeyword.
  - `storeSearchRecord(self, discord_id, title, keyword, map_rate, tag, map_address) -> int`: Method storeSearchRecord.
  - `getSearchRecoreds(self, discord_id) -> list`: Method getSearchRecoreds.
  - `updateRecordRate(self, id, new_rate) -> bool`: Method updateRecordRate.
  - `getRecentRecords(self, discord_id, days) -> list`: 取得最近 N 天內的搜尋記錄，用於避免重複推薦
  - `getLikedRecords(self, discord_id) -> list`: 取得 self_rate >= 1 的記錄（用戶喜歡的）
  - `getDislikedRecords(self, discord_id) -> list`: 取得 self_rate <= -1 的記錄（用戶不喜歡的）

## Functions

None
