# File: `cogs/story/manager.py`

## Overview
Core responsibilities and logic for `cogs/story/manager.py`. This module is part of the cogs subsystem and handles the associated business logic, state management, and integrations.

## Classes

### `StoryManager`
The core manager for story logic. It coordinates the database, state,
and prompt engine to generate story progression based on the v5 layered AI agent architecture.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `cog` (`Any`): Instance attribute managing cog.
  - `logger` (`Any`): Instance attribute managing logger.
  - `system_prompt_manager` (`Any`): Instance attribute managing system_prompt_manager.
  - `_initialized` (`Any`): Instance attribute managing _initialized.
  - `character_db` (`Any`): Instance attribute managing character_db.
  - `prompt_engine` (`Any`): Instance attribute managing prompt_engine.
  - `state_manager` (`Any`): Instance attribute managing state_manager.

- **Methods**:
  - `initialize() -> Any`: Initializes the StoryManager and its components.
  - `add_intervention(channel_id, text) -> Any`: Stores an intervention for a specific channel.
  - `intervene(interaction) -> Any`: Opens a modal for the user to provide an OOC intervention.
  - `process_story_message(message) -> Any`: Processes a message from a story channel using the v5 layered agent architecture. This method acts as the central orchestrator.
  - `start_story(interaction, world_name, character_ids, use_narrator, initial_date, initial_time, initial_location) -> Any`: Handles the logic of starting a new story, creating the instance, and generating the first scene.
  - `generate_first_scene(interaction, story_instance) -> Any`: Generates the introductory scene for a new story using the v5 architecture.

