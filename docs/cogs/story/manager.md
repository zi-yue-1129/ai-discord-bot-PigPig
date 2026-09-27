# File: `cogs/story/manager.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `manager` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `StoryManager`
The core manager for story logic. It coordinates the database, state,
and prompt engine to generate story progression based on the v5 layered AI agent architecture.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `cog` (`Any`): Instance attribute for cog.
  - `logger` (`Any`): Instance attribute for logger.
  - `system_prompt_manager` (`Any`): Instance attribute for system_prompt_manager.
  - `_initialized` (`Any`): Instance attribute for _initialized.
  - `db_instances` (`Dict[...]`): Instance attribute for db_instances.
  - `character_db` (`Any`): Instance attribute for character_db.
  - `prompt_engine` (`Any`): Instance attribute for prompt_engine.
  - `state_manager` (`Any`): Instance attribute for state_manager.
  - `language_manager` (`LanguageManager`): Instance attribute for language_manager.
  - `interventions` (`Dict[...]`): Instance attribute for interventions.

- **Methods**:
  - `__init__(bot, cog, system_prompt_manager) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `CharacterDB` and `StoryPromptEngine`.
  - `_get_db(guild_id) -> StoryDB`: Gets or creates a database connection for a specific guild.
  - `_extract_structured_response(response, expected_model, context) -> Optional[...]`: Unified extractor for structured agent responses.
  - `initialize() -> Any`: Initializes the StoryManager and its components.
  - `add_intervention(channel_id, text) -> Any`: Stores an intervention for a specific channel.
  - `intervene(interaction) -> Any`: Opens a modal for the user to provide an OOC intervention.
  - `_update_relationships(db, story_id, updates) -> Any`: Updates player-NPC relationships based on the GM plan.
  - `_record_event(db, world, instance, gm_plan, final_content) -> Any`: Creates and records an event in the world state.
  - `_send_story_response(channel, character, story_instance, content) -> Any`: Constructs and sends the story response as an embed, using a webhook if available.
  - `process_story_message(message) -> Any`: Processes a message from a story channel using the v5 layered agent architecture.
  - `_find_speaking_character(speaker_name, characters, channel) -> Optional[...]`: Unified character lookup logic, supports multiple matching methods.
  - `_generate_and_save_summary(story_instance) -> Any`: Generates a summary of the last 20-40 messages and saves it.
  - `_generate_and_save_outline(story_instance) -> Any`: Generates a high-level outline from the last 10 summaries and saves it.
  - `start_story(interaction, world_name, character_ids, use_narrator, initial_date, initial_time, initial_location) -> Any`: Handles the logic of starting a new story, creating the instance,
  - `generate_first_scene(interaction, story_instance) -> Any`: Generates the introductory scene for a new story using the v5 architecture.
