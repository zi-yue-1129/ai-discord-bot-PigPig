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
  - `discord_id` (`str`): Stores data related to discord_id.
  - `discord_name` (`str`): Stores data related to discord_name.
  - `display_names` (`List[str]`): Stores data related to display_names.
  - `procedural_memory` (`Optional[str]`): Stores data related to procedural_memory.
  - `user_background` (`Optional[str]`): Stores data related to user_background.
  - `created_at` (`Optional[datetime]`): Stores data related to created_at.

- **Methods**:
  - `to_dict() -> Dict[Tuple[str, Any]]`: Convert to dict for serialization; datetimes become ISO strings.
  - `from_dict(cls, data) -> UserInfo`: Instantiate from dict, handling created_at and display_names formats.
