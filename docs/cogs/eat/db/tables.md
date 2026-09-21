# File: `cogs/eat/db/tables.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `UserPref`
Core class implementation.

- **Attributes**:
  - None specified.

- **Methods**:
  - None specified.

### `SearchRecord`
Core class implementation.

- **Attributes**:
  - `discord_id` (`Any`): Attribute holding discord_id data.
  - `keyword` (`Any`): Attribute holding keyword data.
  - `title` (`Any`): Attribute holding title data.
  - `tag` (`Any`): Attribute holding tag data.
  - `address` (`Any`): Attribute holding address data.
  - `map_rate` (`Any`): Attribute holding map_rate data.
  - `self_rate` (`Any`): Attribute holding self_rate data.
  - `date` (`Any`): Attribute holding date data.

- **Methods**:
  - `__init__(discord_id: str, title: str, keyword: str, tag: str, address: str, map_rate: str, self_rate: float) -> Any`: Executes __init__ logic.

### `Keywords`
Core class implementation.

- **Attributes**:
  - `keyword` (`Any`): Attribute holding keyword data.
  - `add_date` (`Any`): Attribute holding add_date data.

- **Methods**:
  - `__init__(keyword: String) -> Any`: Executes __init__ logic.

## Functions

No top-level functions defined.
