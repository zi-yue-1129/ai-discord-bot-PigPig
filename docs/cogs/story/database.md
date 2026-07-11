# File: `cogs/story/database.py`

## Overview
This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `database.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `CharacterDB`
Handles all database operations for characters, independent of story worlds.

- **Attributes**:
  - `db_path` (`Any`): Internal instance state.
  - `_initialized` (`Any`): Internal instance state.
  - `_lock` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__() -> Any`: Performs internal processing logic.
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
  - `db_path` (`Any`): Internal instance state.
  - `guild_id` (`Any`): Internal instance state.
  - `_initialized` (`Any`): Internal instance state.
  - `_lock` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(guild_id: int) -> Any`: Performs internal processing logic.
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


## Handwritten Context
# Story System - Database

**File:** [`cogs/story/database.py`](cogs/story/database.py)

This module handles all data persistence for the story system. It is uniquely designed with two separate database classes to manage global and server-specific data.

## `CharacterDB` Class (Global)

This class manages a single, global database file: `data/story/characters.db`. This database stores all characters created across all servers the bot is in.

*   **Purpose:** To create a shared repository of characters. A character created on one server can potentially be used in another, depending on its `is_public` flag.
*   **Key Methods:**
    *   `save_character(...)`: Saves or updates a `StoryCharacter` object.
    *   `get_character(...)`: Retrieves a single character by its unique ID.
    *   `get_characters_by_guild(...)`: Retrieves all characters associated with a specific server.
    *   `get_selectable_characters(...)`: Retrieves all characters a specific user is allowed to use in a story. This includes all public characters in the server plus any private characters created by that user.
    *   `delete_character(...)`: Deletes a character from the database.

## `StoryDB` Class (Per-Guild)

This class manages a separate database file for each server (guild), located at `data/story/{guild_id}_story.db`.

*   **Purpose:** To keep all story-related data completely isolated between servers. One server's worlds, ongoing stories, and character relationships cannot be accessed by another.
*   **Key Methods:**
    *   **World Management:**
        *   `save_world(...)`: Saves or updates a `StoryWorld` object, serializing its complex nested data (locations, events) into JSON format for storage.
        *   `get_world(...)`: Retrieves and deserializes a `StoryWorld` object from the database.
        *   `get_all_worlds()`: Gets a list of all worlds created on that server.
    *   **Instance Management:**
        *   `save_story_instance(...)`: Saves or updates a `StoryInstance`, which represents an active story in a specific channel. This includes the current state, active characters, summaries, and outlines.
        *   `get_story_instance(...)`: Retrieves the active story for a specific channel.
    *   **Relationship Management:**
        *   `save_player_relationship(...)`: Saves or updates the description of the relationship between a player (user) and an NPC (character).
        *   `get_relationships_for_story(...)`: Retrieves all relationship data for an ongoing story.