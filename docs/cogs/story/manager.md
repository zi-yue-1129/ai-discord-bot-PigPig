# File: `cogs/story/manager.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/story/manager.py`.

## Classes

### `StoryManager`
The core manager for story logic. It coordinates the database, state, and prompt engine to generate story progression based on the v5 layered AI agent architecture.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `cog` (`Any`): Instance attribute cog
  - `logger` (`Any`): Instance attribute logger
  - `system_prompt_manager` (`Any`): Instance attribute system_prompt_manager
  - `_initialized` (`Any`): Instance attribute _initialized
  - `db_instances` (`Dict[int, StoryDB]`): Instance attribute db_instances
  - `character_db` (`Any`): Instance attribute character_db
  - `prompt_engine` (`Any`): Instance attribute prompt_engine
  - `state_manager` (`Any`): Instance attribute state_manager
  - `language_manager` (`LanguageManager`): Instance attribute language_manager
  - `interventions` (`Dict[int, str]`): Instance attribute interventions

- **Methods**:
  - `_get_db(self, guild_id) -> StoryDB`: Gets or creates a database connection for a specific guild.
  - `_extract_structured_response(self, response, expected_model, context) -> Optional[T]`: Unified extractor for structured agent responses.  Args:     response: Raw response returned by agent.ainvoke()     expected_model: Expected Pydantic model class     context: Logging context (e.g., "GM Agent", "Character Agent")  Returns:     Parsed model instance on success, None on failure.
  - `initialize(self) -> Any`: Initializes the StoryManager and its components.
  - `add_intervention(self, channel_id, text) -> Any`: Stores an intervention for a specific channel.
  - `intervene(self, interaction) -> Any`: Opens a modal for the user to provide an OOC intervention.
  - `_update_relationships(self, db, story_id, updates) -> Any`: Updates player-NPC relationships based on the GM plan.
  - `_record_event(self, db, world, instance, gm_plan, final_content) -> Any`: Creates and records an event in the world state.
  - `_send_story_response(self, channel, character, story_instance, content) -> Any`: Constructs and sends the story response as an embed, using a webhook if available.
  - `process_story_message(self, message) -> Any`: Processes a message from a story channel using the v5 layered agent architecture. This method acts as the central orchestrator.
  - `_find_speaking_character(self, speaker_name, characters, channel) -> Optional[StoryCharacter]`: Unified character lookup logic, supports multiple matching methods.
  - `_generate_and_save_summary(self, story_instance) -> Any`: Generates a summary of the last 20-40 messages and saves it. Uses structured output (StorySummary).
  - `_generate_and_save_outline(self, story_instance) -> Any`: Generates a high-level outline from the last 10 summaries and saves it. Uses structured output (StoryOutline).
  - `start_story(self, interaction, world_name, character_ids, use_narrator, initial_date, initial_time, initial_location) -> Any`: Handles the logic of starting a new story, creating the instance, and generating the first scene.
  - `generate_first_scene(self, interaction, story_instance) -> Any`: Generates the introductory scene for a new story using the v5 architecture.

## Functions

None

