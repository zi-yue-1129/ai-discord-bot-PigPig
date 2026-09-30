# File: `cogs/story/models.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/story/models.py`.

## Classes

### `Event`
Represents a specific event that occurred at a location.

- **Attributes**:
  - `title` (`str`): Attribute title
  - `summary` (`str`): Attribute summary
  - `full_content` (`str`): Attribute full_content
  - `timestamp` (`str`): Attribute timestamp

- **Methods**:
  - None

### `Location`
Represents a specific location within the story world.

- **Attributes**:
  - `name` (`str`): Attribute name
  - `events` (`List[Event]`): Attribute events
  - `attributes` (`Dict[str, Any]`): Attribute attributes

- **Methods**:
  - None

### `StoryWorld`
Represents the lore and rules of a story world, acting as a container for locations.

- **Attributes**:
  - `guild_id` (`int`): Attribute guild_id
  - `world_name` (`str`): Attribute world_name
  - `locations` (`List[Location]`): Attribute locations
  - `attributes` (`Dict[str, Any]`): Attribute attributes

- **Methods**:
  - None

### `StoryCharacter`
Represents a character, either player-controlled (PC) or non-player (NPC).

- **Attributes**:
  - `name` (`str`): Attribute name
  - `description` (`str`): Attribute description
  - `guild_id` (`int`): Attribute guild_id
  - `creator_id` (`int`): Attribute creator_id
  - `is_pc` (`bool`): Attribute is_pc
  - `user_id` (`Optional[int]`): Attribute user_id
  - `is_public` (`bool`): Attribute is_public
  - `webhook_url` (`Optional[str]`): Attribute webhook_url
  - `attributes` (`Dict[str, Any]`): Attribute attributes
  - `inventory` (`List[str]`): Attribute inventory
  - `status` (`str`): Attribute status
  - `character_id` (`str`): Attribute character_id

- **Methods**:
  - None

### `StoryInstance`
Represents an active story session in a specific channel.

- **Attributes**:
  - `channel_id` (`int`): Attribute channel_id
  - `guild_id` (`int`): Attribute guild_id
  - `world_name` (`str`): Attribute world_name
  - `current_date` (`Optional[str]`): Attribute current_date
  - `current_time` (`Optional[str]`): Attribute current_time
  - `current_location` (`str`): Attribute current_location
  - `is_active` (`bool`): Attribute is_active
  - `active_character_ids` (`List[str]`): Attribute active_character_ids
  - `current_state` (`Dict[str, Any]`): Attribute current_state
  - `event_log` (`List[str]`): Attribute event_log
  - `message_counter` (`int`): Attribute message_counter
  - `summaries` (`List[str]`): Attribute summaries
  - `outlines` (`List[str]`): Attribute outlines
  - `narration_enabled` (`bool`): Attribute narration_enabled

- **Methods**:
  - None

### `PlayerRelationship`
Represents the relationship between a player (user) and an NPC.

- **Attributes**:
  - `story_id` (`int`): Attribute story_id
  - `character_id` (`str`): Attribute character_id
  - `user_id` (`int`): Attribute user_id
  - `description` (`str`): Attribute description
  - `relationship_id` (`str`): Attribute relationship_id

- **Methods**:
  - None

### `DialogueContext`
Class representing DialogueContext.

- **Attributes**:
  - `speaker_name` (`str`): Attribute speaker_name
  - `motivation` (`str`): Attribute motivation
  - `emotional_state` (`str`): Attribute emotional_state

- **Methods**:
  - None

### `StateUpdate`
Class representing StateUpdate.

- **Attributes**:
  - `location` (`str`): Attribute location
  - `date` (`str`): Attribute date
  - `time` (`str`): Attribute time

- **Methods**:
  - None

### `RelationshipUpdate`
Class representing RelationshipUpdate.

- **Attributes**:
  - `character_name` (`str`): Attribute character_name
  - `user_name` (`str`): Attribute user_name
  - `description` (`str`): Attribute description

- **Methods**:
  - None

### `GMActionPlan`
The Game Master's action plan, defining the next step in the story. This structure is used for the AI's structured output.

- **Attributes**:
  - `action_type` (`str`): Attribute action_type
  - `event_title` (`str`): Attribute event_title
  - `event_summary` (`str`): Attribute event_summary
  - `state_update` (`Optional[StateUpdate]`): Attribute state_update
  - `narration_content` (`Optional[str]`): Attribute narration_content
  - `dialogue_context` (`Optional[List[DialogueContext]]`): Attribute dialogue_context
  - `relationships_update` (`Optional[List[RelationshipUpdate]]`): Attribute relationships_update

- **Methods**:
  - None

### `CharacterAction`
Represents a character's action, combining dialogue, physical action, and internal thought. This structure is used for the AI's structured output.

- **Attributes**:
  - `action` (`Optional[str]`): Attribute action
  - `dialogue` (`str`): Attribute dialogue
  - `thought` (`Optional[str]`): Attribute thought
  - `location` (`str`): Attribute location
  - `date` (`str`): Attribute date
  - `time` (`str`): Attribute time

- **Methods**:
  - None

### `StorySummary`
Structured output for a story summary

- **Attributes**:
  - `summary` (`str`): Attribute summary
  - `key_events` (`List[str]`): Attribute key_events
  - `character_developments` (`List[str]`): Attribute character_developments

- **Methods**:
  - None

### `StoryOutline`
Structured output for a story outline

- **Attributes**:
  - `outline` (`str`): Attribute outline
  - `major_plot_points` (`List[str]`): Attribute major_plot_points
  - `character_arcs` (`Dict[str, str]`): Attribute character_arcs

- **Methods**:
  - None

## Functions

None
