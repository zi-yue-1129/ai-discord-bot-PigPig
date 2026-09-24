# File: `cogs/story/models.py`

## Overview
Core file handling responsibilities within the `cogs/story` subsystem.

## Classes

### `Event`
Represents a specific event that occurred at a location.

- **Attributes**:
  - `title` (`str`): Class attribute
  - `summary` (`str`): Class attribute
  - `full_content` (`str`): Class attribute
  - `timestamp` (`str`): Class attribute

- **Methods**:
  - None specified.

### `Location`
Represents a specific location within the story world.

- **Attributes**:
  - `name` (`str`): Class attribute
  - `events` (`List[Event]`): Class attribute
  - `attributes` (`Dict[Tuple[str, Any]]`): Class attribute

- **Methods**:
  - None specified.

### `StoryWorld`
Represents the lore and rules of a story world, acting as a container for locations.

- **Attributes**:
  - `guild_id` (`int`): Class attribute
  - `world_name` (`str`): Class attribute
  - `locations` (`List[Location]`): Class attribute
  - `attributes` (`Dict[Tuple[str, Any]]`): Class attribute

- **Methods**:
  - None specified.

### `StoryCharacter`
Represents a character, either player-controlled (PC) or non-player (NPC).

- **Attributes**:
  - `name` (`str`): Class attribute
  - `description` (`str`): Class attribute
  - `guild_id` (`int`): Class attribute
  - `creator_id` (`int`): Class attribute
  - `is_pc` (`bool`): Class attribute
  - `user_id` (`Optional[int]`): Class attribute
  - `is_public` (`bool`): Class attribute
  - `webhook_url` (`Optional[str]`): Class attribute
  - `attributes` (`Dict[Tuple[str, Any]]`): Class attribute
  - `inventory` (`List[str]`): Class attribute
  - `status` (`str`): Class attribute
  - `character_id` (`str`): Class attribute

- **Methods**:
  - None specified.

### `StoryInstance`
Represents an active story session in a specific channel.

- **Attributes**:
  - `channel_id` (`int`): Class attribute
  - `guild_id` (`int`): Class attribute
  - `world_name` (`str`): Class attribute
  - `current_date` (`Optional[str]`): Class attribute
  - `current_time` (`Optional[str]`): Class attribute
  - `current_location` (`str`): Class attribute
  - `is_active` (`bool`): Class attribute
  - `active_character_ids` (`List[str]`): Class attribute
  - `current_state` (`Dict[Tuple[str, Any]]`): Class attribute
  - `event_log` (`List[str]`): Class attribute
  - `message_counter` (`int`): Class attribute
  - `summaries` (`List[str]`): Class attribute
  - `outlines` (`List[str]`): Class attribute
  - `narration_enabled` (`bool`): Class attribute

- **Methods**:
  - None specified.

### `PlayerRelationship`
Represents the relationship between a player (user) and an NPC.

- **Attributes**:
  - `story_id` (`int`): Class attribute
  - `character_id` (`str`): Class attribute
  - `user_id` (`int`): Class attribute
  - `description` (`str`): Class attribute
  - `relationship_id` (`str`): Class attribute

- **Methods**:
  - None specified.

### `DialogueContext`
No description provided.

- **Attributes**:
  - `speaker_name` (`str`): Class attribute
  - `motivation` (`str`): Class attribute
  - `emotional_state` (`str`): Class attribute

- **Methods**:
  - None specified.

### `StateUpdate`
No description provided.

- **Attributes**:
  - `location` (`str`): Class attribute
  - `date` (`str`): Class attribute
  - `time` (`str`): Class attribute

- **Methods**:
  - None specified.

### `RelationshipUpdate`
No description provided.

- **Attributes**:
  - `character_name` (`str`): Class attribute
  - `user_name` (`str`): Class attribute
  - `description` (`str`): Class attribute

- **Methods**:
  - None specified.

### `GMActionPlan`
The Game Master's action plan, defining the next step in the story.

- **Attributes**:
  - `action_type` (`str`): Class attribute
  - `event_title` (`str`): Class attribute
  - `event_summary` (`str`): Class attribute
  - `state_update` (`Optional[StateUpdate]`): Class attribute
  - `narration_content` (`Optional[str]`): Class attribute
  - `dialogue_context` (`Optional[List[DialogueContext]]`): Class attribute
  - `relationships_update` (`Optional[List[RelationshipUpdate]]`): Class attribute

- **Methods**:
  - None specified.

### `CharacterAction`
Represents a character's action, combining dialogue, physical action, and internal thought.

- **Attributes**:
  - `action` (`Optional[str]`): Class attribute
  - `dialogue` (`str`): Class attribute
  - `thought` (`Optional[str]`): Class attribute
  - `location` (`str`): Class attribute
  - `date` (`str`): Class attribute
  - `time` (`str`): Class attribute

- **Methods**:
  - None specified.

### `StorySummary`
Structured output for a story summary

- **Attributes**:
  - `summary` (`str`): Class attribute
  - `key_events` (`List[str]`): Class attribute
  - `character_developments` (`List[str]`): Class attribute

- **Methods**:
  - None specified.

### `StoryOutline`
Structured output for a story outline

- **Attributes**:
  - `outline` (`str`): Class attribute
  - `major_plot_points` (`List[str]`): Class attribute
  - `character_arcs` (`Dict[Tuple[str, str]]`): Class attribute

- **Methods**:
  - None specified.

## Functions

No module-level functions defined in this file.
