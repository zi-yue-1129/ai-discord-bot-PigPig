# File: `cogs/eat/train/data_loader.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `data_loader` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `DataLoader`
Represents the `DataLoader` class in the system.

- **Attributes**:
  - `db` (`Any`): Instance attribute for db.

- **Methods**:
  - `__init__(db) -> None`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `loadingData(discord_id) -> Any`: Handles the `loadingData` functionality. Internally, it interacts with methods like `getSearchRecoreds`.
  - `procressData(data) -> Any`: Handles the `procressData` functionality. Internally, it interacts with methods like `lcut_for_search` and `append`.
  - `genVocabularyList(data) -> Any`: Handles the `genVocabularyList` functionality. Internally, it interacts with methods like `sorted` and `add`.
  - `transform(data, voc_length, batch_size) -> Any`: Handles the `transform` functionality. Internally, it interacts with methods like `genVocabularyList` and `range`.
