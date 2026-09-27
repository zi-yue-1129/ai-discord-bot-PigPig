# File: `cogs/story/models.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `models` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `Event`
Represents a specific event that occurred at a location.

- **Attributes**:
  - `title` (`str`): Class attribute representing title.
  - `summary` (`str`): Class attribute representing summary.
  - `full_content` (`str`): Class attribute representing full_content.
  - `timestamp` (`str`): Class attribute representing timestamp.

### `Location`
Represents a specific location within the story world.

- **Attributes**:
  - `name` (`str`): Class attribute representing name.
  - `events` (`List[...]`): Class attribute representing events.
  - `attributes` (`Dict[...]`): Class attribute representing attributes.

### `StoryWorld`
Represents the lore and rules of a story world, acting as a container for locations.

- **Attributes**:
  - `guild_id` (`int`): Class attribute representing guild_id.
  - `world_name` (`str`): Class attribute representing world_name.
  - `locations` (`List[...]`): Class attribute representing locations.
  - `attributes` (`Dict[...]`): Class attribute representing attributes.

### `StoryCharacter`
Represents a character, either player-controlled (PC) or non-player (NPC).

- **Attributes**:
  - `name` (`str`): Class attribute representing name.
  - `description` (`str`): Class attribute representing description.
  - `guild_id` (`int`): Class attribute representing guild_id.
  - `creator_id` (`int`): Class attribute representing creator_id.
  - `is_pc` (`bool`): Class attribute representing is_pc.
  - `user_id` (`Optional[...]`): Class attribute representing user_id.
  - `is_public` (`bool`): Class attribute representing is_public.
  - `webhook_url` (`Optional[...]`): Class attribute representing webhook_url.
  - `attributes` (`Dict[...]`): Class attribute representing attributes.
  - `inventory` (`List[...]`): Class attribute representing inventory.
  - `status` (`str`): Class attribute representing status.
  - `character_id` (`str`): Class attribute representing character_id.

### `StoryInstance`
Represents an active story session in a specific channel.

- **Attributes**:
  - `channel_id` (`int`): Class attribute representing channel_id.
  - `guild_id` (`int`): Class attribute representing guild_id.
  - `world_name` (`str`): Class attribute representing world_name.
  - `current_date` (`Optional[...]`): Class attribute representing current_date.
  - `current_time` (`Optional[...]`): Class attribute representing current_time.
  - `current_location` (`str`): Class attribute representing current_location.
  - `is_active` (`bool`): Class attribute representing is_active.
  - `active_character_ids` (`List[...]`): Class attribute representing active_character_ids.
  - `current_state` (`Dict[...]`): Class attribute representing current_state.
  - `event_log` (`List[...]`): Class attribute representing event_log.
  - `message_counter` (`int`): Class attribute representing message_counter.
  - `summaries` (`List[...]`): Class attribute representing summaries.
  - `outlines` (`List[...]`): Class attribute representing outlines.
  - `narration_enabled` (`bool`): Class attribute representing narration_enabled.

### `PlayerRelationship`
Represents the relationship between a player (user) and an NPC.

- **Attributes**:
  - `story_id` (`int`): Class attribute representing story_id.
  - `character_id` (`str`): Class attribute representing character_id.
  - `user_id` (`int`): Class attribute representing user_id.
  - `description` (`str`): Class attribute representing description.
  - `relationship_id` (`str`): Class attribute representing relationship_id.

### `DialogueContext`
Represents the `DialogueContext` class in the system.

- **Attributes**:
  - `speaker_name` (`str`): Class attribute representing speaker_name.
  - `motivation` (`str`): Class attribute representing motivation.
  - `emotional_state` (`str`): Class attribute representing emotional_state.

### `StateUpdate`
Represents the `StateUpdate` class in the system.

- **Attributes**:
  - `location` (`str`): Class attribute representing location.
  - `date` (`str`): Class attribute representing date.
  - `time` (`str`): Class attribute representing time.

### `RelationshipUpdate`
Represents the `RelationshipUpdate` class in the system.

- **Attributes**:
  - `character_name` (`str`): Class attribute representing character_name.
  - `user_name` (`str`): Class attribute representing user_name.
  - `description` (`str`): Class attribute representing description.

### `GMActionPlan`
The Game Master's action plan, defining the next step in the story.
This structure is used for the AI's structured output.

- **Attributes**:
  - `action_type` (`str`): Class attribute representing action_type.
  - `event_title` (`str`): Class attribute representing event_title.
  - `event_summary` (`str`): Class attribute representing event_summary.
  - `state_update` (`Optional[...]`): Class attribute representing state_update.
  - `narration_content` (`Optional[...]`): Class attribute representing narration_content.
  - `dialogue_context` (`Optional[...]`): Class attribute representing dialogue_context.
  - `relationships_update` (`Optional[...]`): Class attribute representing relationships_update.

### `CharacterAction`
Represents a character's action, combining dialogue, physical action, and internal thought.
This structure is used for the AI's structured output.

- **Attributes**:
  - `action` (`Optional[...]`): Class attribute representing action.
  - `dialogue` (`str`): Class attribute representing dialogue.
  - `thought` (`Optional[...]`): Class attribute representing thought.
  - `location` (`str`): Class attribute representing location.
  - `date` (`str`): Class attribute representing date.
  - `time` (`str`): Class attribute representing time.

### `StorySummary`
Structured output for a story summary

- **Attributes**:
  - `summary` (`str`): Class attribute representing summary.
  - `key_events` (`List[...]`): Class attribute representing key_events.
  - `character_developments` (`List[...]`): Class attribute representing character_developments.

### `StoryOutline`
Structured output for a story outline

- **Attributes**:
  - `outline` (`str`): Class attribute representing outline.
  - `major_plot_points` (`List[...]`): Class attribute representing major_plot_points.
  - `character_arcs` (`Dict[...]`): Class attribute representing character_arcs.
