# File: `cogs/eat/db/tables.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `tables` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `UserPref`
Represents the `UserPref` class in the system.

- **Attributes**:
  - `__tablename__` (`Any`): Class attribute representing __tablename__.
  - `id` (`Any`): Class attribute representing id.
  - `discord_id` (`Any`): Class attribute representing discord_id.
  - `model_uri` (`Any`): Class attribute representing model_uri.
  - `last_update` (`Any`): Class attribute representing last_update.

### `SearchRecord`
Represents the `SearchRecord` class in the system.

- **Attributes**:
  - `__tablename__` (`Any`): Class attribute representing __tablename__.
  - `id` (`Any`): Class attribute representing id.
  - `date` (`Any`): Class attribute representing date.
  - `discord_id` (`Any`): Class attribute representing discord_id.
  - `title` (`Any`): Class attribute representing title.
  - `tag` (`Any`): Class attribute representing tag.
  - `address` (`Any`): Class attribute representing address.
  - `keyword` (`Any`): Class attribute representing keyword.
  - `map_rate` (`Any`): Class attribute representing map_rate.
  - `self_rate` (`Any`): Class attribute representing self_rate.

- **Methods**:
  - `__init__(discord_id, title, keyword, tag, address, map_rate, self_rate) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `timestamp` and `now`.

### `Keywords`
Represents the `Keywords` class in the system.

- **Attributes**:
  - `__tablename__` (`Any`): Class attribute representing __tablename__.
  - `id` (`Any`): Class attribute representing id.
  - `keyword` (`Any`): Class attribute representing keyword.
  - `add_date` (`Any`): Class attribute representing add_date.

- **Methods**:
  - `__init__(keyword) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `timestamp` and `now`.
