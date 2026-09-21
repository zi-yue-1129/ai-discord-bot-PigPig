# File: `cogs/eat/train/data_loader.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `DataLoader`
Core class implementation.

- **Attributes**:
  - `db` (`Any`): Attribute holding db data.

- **Methods**:
  - `__init__(db: DB) -> None`: Executes __init__ logic.
  - `loadingData(discord_id: str) -> Any`: Executes loadingData logic.
  - `procressData(data) -> Any`: Executes procressData logic.
  - `genVocabularyList(data) -> Any`: Executes genVocabularyList logic.
  - `transform(data, voc_length, batch_size) -> Any`: Executes transform logic.

## Functions

No top-level functions defined.
