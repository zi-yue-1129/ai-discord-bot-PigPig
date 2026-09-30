# File: `cogs/story/database.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/story/database.py`.

## Classes

### `CharacterDB`
Handles all database operations for characters, independent of story worlds.

- **Attributes**:
  - `db_path` (`Any`): Instance attribute db_path
  - `_initialized` (`Any`): Instance attribute _initialized
  - `_lock` (`Any`): Instance attribute _lock
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `_get_connection(self) -> sqlite3.Connection`: Establishes and returns a database connection.
  - `initialize(self) -> Any`: Initializes the character database, creates the table, and handles migrations.
  - `save_character(self, character) -> Any`: Saves or updates a character.
  - `_row_to_character(self, row) -> StoryCharacter`: Converts a database row to a StoryCharacter object.
  - `get_character(self, character_id) -> Optional[StoryCharacter]`: Retrieves a character by ID.
  - `get_characters_by_user(self, user_id, guild_id) -> List[StoryCharacter]`: Retrieves all characters created by a user in a specific guild.
  - `get_characters_by_guild(self, guild_id) -> List[StoryCharacter]`: Retrieves all characters for a specific guild.
  - `get_selectable_characters(self, guild_id, user_id) -> List[StoryCharacter]`: Retrieves all characters that a user can select in a guild.  This includes all public characters in the guild and all private characters created by the user.
  - `get_characters_by_ids(self, character_ids) -> List[StoryCharacter]`: Retrieves multiple characters by their IDs.  Args:     character_ids: List of character ID strings (UUIDs)      Returns:     List of StoryCharacter objects
  - `delete_character(self, character_id) -> Any`: Deletes a character by ID.

### `StoryDB`
Handles all database operations for the story module (worlds and instances).

- **Attributes**:
  - `db_path` (`Any`): Instance attribute db_path
  - `guild_id` (`Any`): Instance attribute guild_id
  - `_initialized` (`Any`): Instance attribute _initialized
  - `_lock` (`Any`): Instance attribute _lock
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `_get_connection(self) -> sqlite3.Connection`: Establishes and returns a database connection.
  - `initialize(self) -> Any`: Initializes the database and creates tables if they don't exist.
  - `save_world(self, world) -> Any`: Saves or updates a story world using a SELECT then INSERT/UPDATE strategy.
  - `get_world(self, world_name) -> Optional[StoryWorld]`: Retrieves a story world by name.
  - `get_all_worlds(self) -> List[StoryWorld]`: Retrieves all story worlds for this guild.
  - `save_story_instance(self, instance) -> Any`: Saves or updates a story instance.
  - `get_story_instance(self, channel_id) -> Optional[StoryInstance]`: Retrieves a story instance by channel ID.
  - `save_player_relationship(self, relationship) -> Any`: Saves or updates a player-NPC relationship.
  - `get_player_relationship(self, relationship_id) -> Optional[PlayerRelationship]`: Retrieves a player-NPC relationship by ID.
  - `get_relationships_for_story(self, story_id) -> List[PlayerRelationship]`: Retrieves all relationships for a given story instance.

## Functions

None

