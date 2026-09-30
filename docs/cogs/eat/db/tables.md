# File: `cogs/eat/db/tables.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/eat/db/tables.py`.

## Classes

### `UserPref`
Class representing UserPref.

- **Attributes**:
  - `__tablename__` (`Any`): Attribute __tablename__
  - `id` (`Any`): Attribute id
  - `discord_id` (`Any`): Attribute discord_id
  - `model_uri` (`Any`): Attribute model_uri
  - `last_update` (`Any`): Attribute last_update

- **Methods**:
  - None

### `SearchRecord`
Class representing SearchRecord.

- **Attributes**:
  - `__tablename__` (`Any`): Attribute __tablename__
  - `id` (`Any`): Attribute id
  - `date` (`Any`): Attribute date
  - `discord_id` (`Any`): Attribute discord_id
  - `title` (`Any`): Attribute title
  - `tag` (`Any`): Attribute tag
  - `address` (`Any`): Attribute address
  - `keyword` (`Any`): Attribute keyword
  - `map_rate` (`Any`): Attribute map_rate
  - `self_rate` (`Any`): Attribute self_rate

- **Methods**:
  - None

### `Keywords`
Class representing Keywords.

- **Attributes**:
  - `__tablename__` (`Any`): Attribute __tablename__
  - `id` (`Any`): Attribute id
  - `keyword` (`Any`): Attribute keyword
  - `add_date` (`Any`): Attribute add_date

- **Methods**:
  - None

## Functions

None
