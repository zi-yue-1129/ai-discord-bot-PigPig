# File: `cogs/story/models.py`

## Overview
Core logic and functionalities for models.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Classes

### `Event`
Represents a specific event that occurred at a location.

- **Attributes**:
  - `title` (`str`): Stores data related to title.
  - `summary` (`str`): Stores data related to summary.
  - `full_content` (`str`): Stores data related to full_content.
  - `timestamp` (`str`): Stores data related to timestamp.

### `Location`
Represents a specific location within the story world.

- **Attributes**:
  - `name` (`str`): Stores data related to name.
  - `events` (`List[Event]`): Stores data related to events.
  - `attributes` (`Dict[Tuple[str, Any]]`): Stores data related to attributes.

### `StoryWorld`
Represents the lore and rules of a story world, acting as a container for locations.

- **Attributes**:
  - `guild_id` (`int`): Stores data related to guild_id.
  - `world_name` (`str`): Stores data related to world_name.
  - `locations` (`List[Location]`): Stores data related to locations.
  - `attributes` (`Dict[Tuple[str, Any]]`): Stores data related to attributes.

### `StoryCharacter`
Represents a character, either player-controlled (PC) or non-player (NPC).

- **Attributes**:
  - `name` (`str`): Stores data related to name.
  - `description` (`str`): Stores data related to description.
  - `guild_id` (`int`): Stores data related to guild_id.
  - `creator_id` (`int`): Stores data related to creator_id.
  - `is_pc` (`bool`): Stores data related to is_pc.
  - `user_id` (`Optional[int]`): Stores data related to user_id.
  - `is_public` (`bool`): Stores data related to is_public.
  - `webhook_url` (`Optional[str]`): Stores data related to webhook_url.
  - `attributes` (`Dict[Tuple[str, Any]]`): Stores data related to attributes.
  - `inventory` (`List[str]`): Stores data related to inventory.
  - `status` (`str`): Stores data related to status.
  - `character_id` (`str`): Stores data related to character_id.

### `StoryInstance`
Represents an active story session in a specific channel.

- **Attributes**:
  - `channel_id` (`int`): Stores data related to channel_id.
  - `guild_id` (`int`): Stores data related to guild_id.
  - `world_name` (`str`): Stores data related to world_name.
  - `current_date` (`Optional[str]`): Stores data related to current_date.
  - `current_time` (`Optional[str]`): Stores data related to current_time.
  - `current_location` (`str`): Stores data related to current_location.
  - `is_active` (`bool`): Stores data related to is_active.
  - `active_character_ids` (`List[str]`): Stores data related to active_character_ids.
  - `current_state` (`Dict[Tuple[str, Any]]`): Stores data related to current_state.
  - `event_log` (`List[str]`): Stores data related to event_log.
  - `message_counter` (`int`): Stores data related to message_counter.
  - `summaries` (`List[str]`): Stores data related to summaries.
  - `outlines` (`List[str]`): Stores data related to outlines.
  - `narration_enabled` (`bool`): Stores data related to narration_enabled.

### `PlayerRelationship`
Represents the relationship between a player (user) and an NPC.

- **Attributes**:
  - `story_id` (`int`): Stores data related to story_id.
  - `character_id` (`str`): Stores data related to character_id.
  - `user_id` (`int`): Stores data related to user_id.
  - `description` (`str`): Stores data related to description.
  - `relationship_id` (`str`): Stores data related to relationship_id.

### `DialogueContext`
Represents DialogueContext.

- **Attributes**:
  - `speaker_name` (`str`): Stores data related to speaker_name.
  - `motivation` (`str`): Stores data related to motivation.
  - `emotional_state` (`str`): Stores data related to emotional_state.

### `StateUpdate`
Represents StateUpdate.

- **Attributes**:
  - `location` (`str`): Stores data related to location.
  - `date` (`str`): Stores data related to date.
  - `time` (`str`): Stores data related to time.

### `RelationshipUpdate`
Represents RelationshipUpdate.

- **Attributes**:
  - `character_name` (`str`): Stores data related to character_name.
  - `user_name` (`str`): Stores data related to user_name.
  - `description` (`str`): Stores data related to description.

### `GMActionPlan`
The Game Master's action plan, defining the next step in the story.
This structure is used for the AI's structured output.

- **Attributes**:
  - `action_type` (`str`): Stores data related to action_type.
  - `event_title` (`str`): Stores data related to event_title.
  - `event_summary` (`str`): Stores data related to event_summary.
  - `state_update` (`Optional[StateUpdate]`): Stores data related to state_update.
  - `narration_content` (`Optional[str]`): Stores data related to narration_content.
  - `dialogue_context` (`Optional[List[DialogueContext]]`): Stores data related to dialogue_context.
  - `relationships_update` (`Optional[List[RelationshipUpdate]]`): Stores data related to relationships_update.

### `CharacterAction`
Represents a character's action, combining dialogue, physical action, and internal thought.
This structure is used for the AI's structured output.

- **Attributes**:
  - `action` (`Optional[str]`): Stores data related to action.
  - `dialogue` (`str`): Stores data related to dialogue.
  - `thought` (`Optional[str]`): Stores data related to thought.
  - `location` (`str`): Stores data related to location.
  - `date` (`str`): Stores data related to date.
  - `time` (`str`): Stores data related to time.

### `StorySummary`
Structured output for a story summary

- **Attributes**:
  - `summary` (`str`): Stores data related to summary.
  - `key_events` (`List[str]`): Stores data related to key_events.
  - `character_developments` (`List[str]`): Stores data related to character_developments.

### `StoryOutline`
Structured output for a story outline

- **Attributes**:
  - `outline` (`str`): Stores data related to outline.
  - `major_plot_points` (`List[str]`): Stores data related to major_plot_points.
  - `character_arcs` (`Dict[Tuple[str, str]]`): Stores data related to character_arcs.
