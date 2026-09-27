# File: `cogs/eat/db/db.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `db` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `DB`
Represents the `DB` class in the system.

- **Attributes**:
  - `engine` (`Any`): Instance attribute for engine.

- **Methods**:
  - `__init__() -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `create_engine` and `create_all`.
  - `getKeywords() -> list`: Handles the `getKeywords` functionality. Internally, it interacts with methods like `select` and `Session`.
  - `checkKeyword(keyword) -> Any`: Handles the `checkKeyword` functionality. Internally, it interacts with methods like `where` and `Session`.
  - `storeKeyword(keyword) -> None`: Handles the `storeKeyword` functionality. Internally, it interacts with methods like `Keywords` and `Session`.
  - `storeSearchRecord(discord_id, title, keyword, map_rate, tag, map_address) -> int`: Handles the `storeSearchRecord` functionality. Internally, it interacts with methods like `SearchRecord` and `Session`.
  - `getSearchRecoreds(discord_id) -> list`: Handles the `getSearchRecoreds` functionality. Internally, it interacts with methods like `where` and `Session`.
  - `updateRecordRate(id, new_rate) -> bool`: Handles the `updateRecordRate` functionality. Internally, it interacts with methods like `Session` and `get`.
  - `getRecentRecords(discord_id, days) -> list`: 取得最近 N 天內的搜尋記錄，用於避免重複推薦
  - `getLikedRecords(discord_id) -> list`: 取得 self_rate >= 1 的記錄（用戶喜歡的）
  - `getDislikedRecords(discord_id) -> list`: 取得 self_rate <= -1 的記錄（用戶不喜歡的）
