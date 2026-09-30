# File: `cogs/memory/users/models.py`

## Overview
UserInfo model for user data.

## Classes

### `UserInfo`
Dataclass matching the new `users` schema.  Fields:   - discord_id: primary identifier (TEXT)   - discord_name: current display name   - display_names: historical display names (stored as JSON array)   - procedural_memory: free-form procedural memory (string)   - user_background: free-form background info (string)   - created_at: creation timestamp

- **Attributes**:
  - `discord_id` (`str`): Attribute discord_id
  - `discord_name` (`str`): Attribute discord_name
  - `display_names` (`List[str]`): Attribute display_names
  - `procedural_memory` (`Optional[str]`): Attribute procedural_memory
  - `user_background` (`Optional[str]`): Attribute user_background
  - `created_at` (`Optional[datetime]`): Attribute created_at

- **Methods**:
  - `to_dict(self) -> Dict[str, Any]`: Convert to dict for serialization; datetimes become ISO strings.
  - `from_dict(cls, data) -> 'UserInfo'`: Instantiate from dict, handling created_at and display_names formats.

## Functions

None
