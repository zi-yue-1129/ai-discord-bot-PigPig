# File: `cogs/memory/users/models.py`

## Overview
UserInfo model for user data.

## Classes

### `UserInfo`
Dataclass matching the new `users` schema.

Fields:
  - discord_id: primary identifier (TEXT)
  - discord_name: current display name
  - display_names: historical display names (stored as JSON array)
  - procedural_memory: free-form procedural memory (string)
  - user_background: free-form background info (string)
  - created_at: creation timestamp

- **Attributes**:
  - `discord_id` (`str`): Class attribute representing discord_id.
  - `discord_name` (`str`): Class attribute representing discord_name.
  - `display_names` (`List[...]`): Class attribute representing display_names.
  - `procedural_memory` (`Optional[...]`): Class attribute representing procedural_memory.
  - `user_background` (`Optional[...]`): Class attribute representing user_background.
  - `created_at` (`Optional[...]`): Class attribute representing created_at.

- **Methods**:
  - `to_dict() -> Dict[...]`: Convert to dict for serialization; datetimes become ISO strings.
  - `from_dict(cls, data) -> UserInfo`: Instantiate from dict, handling created_at and display_names formats.
