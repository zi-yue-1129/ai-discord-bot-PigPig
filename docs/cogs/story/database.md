# File: `cogs/story/database.py`

## Overview
Core file handling responsibilities within the `cogs/story` subsystem.

## Classes

### `CharacterDB`
Handles all database operations for characters, independent of story worlds.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__() -> Any`: No description provided.
  - `_get_connection() -> sqlite3.Connection`: Establishes and returns a database connection.
  - `initialize() -> Any`: Initializes the character database, creates the table, and handles migrations.
  - `save_character(character: StoryCharacter) -> Any`: Saves or updates a character.
  - `_row_to_character(row: sqlite3.Row) -> StoryCharacter`: Converts a database row to a StoryCharacter object.
  - `get_character(character_id: str) -> Optional[StoryCharacter]`: Retrieves a character by ID.
  - `get_characters_by_user(user_id: int, guild_id: int) -> List[StoryCharacter]`: Retrieves all characters created by a user in a specific guild.
  - `get_characters_by_guild(guild_id: int) -> List[StoryCharacter]`: Retrieves all characters for a specific guild.
  - `get_selectable_characters(guild_id: int, user_id: int) -> List[StoryCharacter]`: Retrieves all characters that a user can select in a guild.
  - `get_characters_by_ids(character_ids: List[str]) -> List[StoryCharacter]`: Retrieves multiple characters by their IDs.
  - `delete_character(character_id: str) -> Any`: Deletes a character by ID.

### `StoryDB`
Handles all database operations for the story module (worlds and instances).

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(guild_id: int) -> Any`: No description provided.
  - `_get_connection() -> sqlite3.Connection`: Establishes and returns a database connection.
  - `initialize() -> Any`: Initializes the database and creates tables if they don't exist.
  - `save_world(world: StoryWorld) -> Any`: Saves or updates a story world using a SELECT then INSERT/UPDATE strategy.
  - `get_world(world_name: str) -> Optional[StoryWorld]`: Retrieves a story world by name.
  - `get_all_worlds() -> List[StoryWorld]`: Retrieves all story worlds for this guild.
  - `save_story_instance(instance: StoryInstance) -> Any`: Saves or updates a story instance.
  - `get_story_instance(channel_id: int) -> Optional[StoryInstance]`: Retrieves a story instance by channel ID.
  - `save_player_relationship(relationship: PlayerRelationship) -> Any`: Saves or updates a player-NPC relationship.
  - `get_player_relationship(relationship_id: str) -> Optional[PlayerRelationship]`: Retrieves a player-NPC relationship by ID.
  - `get_relationships_for_story(story_id: int) -> List[PlayerRelationship]`: Retrieves all relationships for a given story instance.

## Functions

No module-level functions defined in this file.

