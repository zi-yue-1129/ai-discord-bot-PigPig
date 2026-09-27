# File: `cogs/story/database.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `database` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `CharacterDB`
Handles all database operations for characters, independent of story worlds.

- **Attributes**:
  - `db_path` (`Any`): Instance attribute for db_path.
  - `_initialized` (`Any`): Instance attribute for _initialized.
  - `_lock` (`Any`): Instance attribute for _lock.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__() -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `Path` and `Lock`.
  - `_get_connection() -> sqlite3.Connection`: Establishes and returns a database connection.
  - `initialize() -> Any`: Initializes the character database, creates the table, and handles migrations.
  - `save_character(character) -> Any`: Saves or updates a character.
  - `_row_to_character(row) -> StoryCharacter`: Converts a database row to a StoryCharacter object.
  - `get_character(character_id) -> Optional[...]`: Retrieves a character by ID.
  - `get_characters_by_user(user_id, guild_id) -> List[...]`: Retrieves all characters created by a user in a specific guild.
  - `get_characters_by_guild(guild_id) -> List[...]`: Retrieves all characters for a specific guild.
  - `get_selectable_characters(guild_id, user_id) -> List[...]`: Retrieves all characters that a user can select in a guild.
  - `get_characters_by_ids(character_ids) -> List[...]`: Retrieves multiple characters by their IDs.
  - `delete_character(character_id) -> Any`: Deletes a character by ID.

### `StoryDB`
Handles all database operations for the story module (worlds and instances).

- **Attributes**:
  - `db_path` (`Any`): Instance attribute for db_path.
  - `guild_id` (`Any`): Instance attribute for guild_id.
  - `_initialized` (`Any`): Instance attribute for _initialized.
  - `_lock` (`Any`): Instance attribute for _lock.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(guild_id) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `Path` and `Lock`.
  - `_get_connection() -> sqlite3.Connection`: Establishes and returns a database connection.
  - `initialize() -> Any`: Initializes the database and creates tables if they don't exist.
  - `save_world(world) -> Any`: Saves or updates a story world using a SELECT then INSERT/UPDATE strategy.
  - `get_world(world_name) -> Optional[...]`: Retrieves a story world by name.
  - `get_all_worlds() -> List[...]`: Retrieves all story worlds for this guild.
  - `save_story_instance(instance) -> Any`: Saves or updates a story instance.
  - `get_story_instance(channel_id) -> Optional[...]`: Retrieves a story instance by channel ID.
  - `save_player_relationship(relationship) -> Any`: Saves or updates a player-NPC relationship.
  - `get_player_relationship(relationship_id) -> Optional[...]`: Retrieves a player-NPC relationship by ID.
  - `get_relationships_for_story(story_id) -> List[...]`: Retrieves all relationships for a given story instance.
