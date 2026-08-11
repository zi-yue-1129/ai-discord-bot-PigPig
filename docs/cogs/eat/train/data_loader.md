# File: `cogs/eat/train/data_loader.py`

## Overview
Core logic and functionalities for data_loader.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Classes

### `DataLoader`
Represents DataLoader.

- **Attributes**:
  - `db` (`Any`): Instance attribute managing db.

- **Methods**:
  - `loadingData(discord_id) -> Any`: Executes loadingData operation.
  - `procressData(data) -> Any`: Executes procressData operation.
  - `genVocabularyList(data) -> Any`: Executes genVocabularyList operation.
  - `transform(data, voc_length, batch_size) -> Any`: Executes transform operation.
