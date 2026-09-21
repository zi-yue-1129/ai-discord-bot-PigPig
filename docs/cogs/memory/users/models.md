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
  - `discord_id` (`str`): Attribute holding discord_id data.
  - `discord_name` (`str`): Attribute holding discord_name data.
  - `display_names` (`List[str]`): Attribute holding display_names data.
  - `procedural_memory` (`Optional[str]`): Attribute holding procedural_memory data.
  - `user_background` (`Optional[str]`): Attribute holding user_background data.
  - `created_at` (`Optional[datetime]`): Attribute holding created_at data.

- **Methods**:
  - `to_dict() -> Dict[Tuple[str, Any]]`: Convert to dict for serialization; datetimes become ISO strings.
  - `from_dict(cls, data: Dict[Tuple[str, Any]]) -> UserInfo`: Instantiate from dict, handling created_at and display_names formats.

## Functions

No top-level functions defined.
