# File: `cogs/story/database.py`

## Overview
Core responsibilities and logic for `cogs/story/database.py`. This module is part of the cogs subsystem and handles the associated business logic, state management, and integrations.

## Classes

### `CharacterDB`
Handles all database operations for characters, independent of story worlds.

- **Attributes**:
  - `db_path` (`Any`): Instance attribute managing db_path.
  - `_initialized` (`Any`): Instance attribute managing _initialized.
  - `_lock` (`Any`): Instance attribute managing _lock.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `initialize() -> Any`: Initializes the character database, creates the table, and handles migrations.
  - `save_character(character) -> Any`: Saves or updates a character.
  - `get_character(character_id) -> Optional[StoryCharacter]`: Retrieves a character by ID.
  - `get_characters_by_user(user_id, guild_id) -> List[StoryCharacter]`: Retrieves all characters created by a user in a specific guild.
  - `get_characters_by_guild(guild_id) -> List[StoryCharacter]`: Retrieves all characters for a specific guild.
  - `get_selectable_characters(guild_id, user_id) -> List[StoryCharacter]`: Retrieves all characters that a user can select in a guild.  This includes all public characters in the guild and all private characters created by the user.
  - `get_characters_by_ids(character_ids) -> List[StoryCharacter]`: Retrieves multiple characters by their IDs.  Args:     character_ids: List of character ID strings (UUIDs)      Returns:     List of StoryCharacter objects
  - `delete_character(character_id) -> Any`: Deletes a character by ID.

### `StoryDB`
Handles all database operations for the story module (worlds and instances).

- **Attributes**:
  - `db_path` (`Any`): Instance attribute managing db_path.
  - `guild_id` (`Any`): Instance attribute managing guild_id.
  - `_initialized` (`Any`): Instance attribute managing _initialized.
  - `_lock` (`Any`): Instance attribute managing _lock.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `initialize() -> Any`: Initializes the database and creates tables if they don't exist.
  - `save_world(world) -> Any`: Saves or updates a story world using a SELECT then INSERT/UPDATE strategy.
  - `get_world(world_name) -> Optional[StoryWorld]`: Retrieves a story world by name.
  - `get_all_worlds() -> List[StoryWorld]`: Retrieves all story worlds for this guild.
  - `save_story_instance(instance) -> Any`: Saves or updates a story instance.
  - `get_story_instance(channel_id) -> Optional[StoryInstance]`: Retrieves a story instance by channel ID.
  - `save_player_relationship(relationship) -> Any`: Saves or updates a player-NPC relationship.
  - `get_player_relationship(relationship_id) -> Optional[PlayerRelationship]`: Retrieves a player-NPC relationship by ID.
  - `get_relationships_for_story(story_id) -> List[PlayerRelationship]`: Retrieves all relationships for a given story instance.

