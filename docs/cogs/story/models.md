# File: `cogs/story/models.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `Event`
Represents a specific event that occurred at a location.

- **Attributes**:
  - `title` (`str`): Attribute holding title data.
  - `summary` (`str`): Attribute holding summary data.
  - `full_content` (`str`): Attribute holding full_content data.
  - `timestamp` (`str`): Attribute holding timestamp data.

- **Methods**:
  - None specified.

### `Location`
Represents a specific location within the story world.

- **Attributes**:
  - `name` (`str`): Attribute holding name data.
  - `events` (`List[Event]`): Attribute holding events data.
  - `attributes` (`Dict[Tuple[str, Any]]`): Attribute holding attributes data.

- **Methods**:
  - None specified.

### `StoryWorld`
Represents the lore and rules of a story world, acting as a container for locations.

- **Attributes**:
  - `guild_id` (`int`): Attribute holding guild_id data.
  - `world_name` (`str`): Attribute holding world_name data.
  - `locations` (`List[Location]`): Attribute holding locations data.
  - `attributes` (`Dict[Tuple[str, Any]]`): Attribute holding attributes data.

- **Methods**:
  - None specified.

### `StoryCharacter`
Represents a character, either player-controlled (PC) or non-player (NPC).

- **Attributes**:
  - `name` (`str`): Attribute holding name data.
  - `description` (`str`): Attribute holding description data.
  - `guild_id` (`int`): Attribute holding guild_id data.
  - `creator_id` (`int`): Attribute holding creator_id data.
  - `is_pc` (`bool`): Attribute holding is_pc data.
  - `user_id` (`Optional[int]`): Attribute holding user_id data.
  - `is_public` (`bool`): Attribute holding is_public data.
  - `webhook_url` (`Optional[str]`): Attribute holding webhook_url data.
  - `attributes` (`Dict[Tuple[str, Any]]`): Attribute holding attributes data.
  - `inventory` (`List[str]`): Attribute holding inventory data.
  - `status` (`str`): Attribute holding status data.
  - `character_id` (`str`): Attribute holding character_id data.

- **Methods**:
  - None specified.

### `StoryInstance`
Represents an active story session in a specific channel.

- **Attributes**:
  - `channel_id` (`int`): Attribute holding channel_id data.
  - `guild_id` (`int`): Attribute holding guild_id data.
  - `world_name` (`str`): Attribute holding world_name data.
  - `current_date` (`Optional[str]`): Attribute holding current_date data.
  - `current_time` (`Optional[str]`): Attribute holding current_time data.
  - `current_location` (`str`): Attribute holding current_location data.
  - `is_active` (`bool`): Attribute holding is_active data.
  - `active_character_ids` (`List[str]`): Attribute holding active_character_ids data.
  - `current_state` (`Dict[Tuple[str, Any]]`): Attribute holding current_state data.
  - `event_log` (`List[str]`): Attribute holding event_log data.
  - `message_counter` (`int`): Attribute holding message_counter data.
  - `summaries` (`List[str]`): Attribute holding summaries data.
  - `outlines` (`List[str]`): Attribute holding outlines data.
  - `narration_enabled` (`bool`): Attribute holding narration_enabled data.

- **Methods**:
  - None specified.

### `PlayerRelationship`
Represents the relationship between a player (user) and an NPC.

- **Attributes**:
  - `story_id` (`int`): Attribute holding story_id data.
  - `character_id` (`str`): Attribute holding character_id data.
  - `user_id` (`int`): Attribute holding user_id data.
  - `description` (`str`): Attribute holding description data.
  - `relationship_id` (`str`): Attribute holding relationship_id data.

- **Methods**:
  - None specified.

### `DialogueContext`
Core class implementation.

- **Attributes**:
  - `speaker_name` (`str`): Attribute holding speaker_name data.
  - `motivation` (`str`): Attribute holding motivation data.
  - `emotional_state` (`str`): Attribute holding emotional_state data.

- **Methods**:
  - None specified.

### `StateUpdate`
Core class implementation.

- **Attributes**:
  - `location` (`str`): Attribute holding location data.
  - `date` (`str`): Attribute holding date data.
  - `time` (`str`): Attribute holding time data.

- **Methods**:
  - None specified.

### `RelationshipUpdate`
Core class implementation.

- **Attributes**:
  - `character_name` (`str`): Attribute holding character_name data.
  - `user_name` (`str`): Attribute holding user_name data.
  - `description` (`str`): Attribute holding description data.

- **Methods**:
  - None specified.

### `GMActionPlan`
The Game Master's action plan, defining the next step in the story.
This structure is used for the AI's structured output.

- **Attributes**:
  - `action_type` (`str`): Attribute holding action_type data.
  - `event_title` (`str`): Attribute holding event_title data.
  - `event_summary` (`str`): Attribute holding event_summary data.
  - `state_update` (`Optional[StateUpdate]`): Attribute holding state_update data.
  - `narration_content` (`Optional[str]`): Attribute holding narration_content data.
  - `dialogue_context` (`Optional[List[DialogueContext]]`): Attribute holding dialogue_context data.
  - `relationships_update` (`Optional[List[RelationshipUpdate]]`): Attribute holding relationships_update data.

- **Methods**:
  - None specified.

### `CharacterAction`
Represents a character's action, combining dialogue, physical action, and internal thought.
This structure is used for the AI's structured output.

- **Attributes**:
  - `action` (`Optional[str]`): Attribute holding action data.
  - `dialogue` (`str`): Attribute holding dialogue data.
  - `thought` (`Optional[str]`): Attribute holding thought data.
  - `location` (`str`): Attribute holding location data.
  - `date` (`str`): Attribute holding date data.
  - `time` (`str`): Attribute holding time data.

- **Methods**:
  - None specified.

### `StorySummary`
Structured output for a story summary

- **Attributes**:
  - `summary` (`str`): Attribute holding summary data.
  - `key_events` (`List[str]`): Attribute holding key_events data.
  - `character_developments` (`List[str]`): Attribute holding character_developments data.

- **Methods**:
  - None specified.

### `StoryOutline`
Structured output for a story outline

- **Attributes**:
  - `outline` (`str`): Attribute holding outline data.
  - `major_plot_points` (`List[str]`): Attribute holding major_plot_points data.
  - `character_arcs` (`Dict[Tuple[str, str]]`): Attribute holding character_arcs data.

- **Methods**:
  - None specified.

## Functions

No top-level functions defined.
