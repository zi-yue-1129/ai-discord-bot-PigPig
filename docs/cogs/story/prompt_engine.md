# File: `cogs/story/prompt_engine.py`

## Overview
Core responsibilities and logic for `cogs/story/prompt_engine.py`. This module is part of the cogs subsystem and handles the associated business logic, state management, and integrations.

## Classes

### `StoryPromptEngine`
Builds high-quality prompts for the layered AI agents in the story.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `logger` (`Any`): Instance attribute managing logger.
  - `system_prompt_manager` (`Any`): Instance attribute managing system_prompt_manager.
  - `language_map` (`Any`): Instance attribute managing language_map.

- **Methods**:
  - `build_gm_prompt(instance, world, characters, user_input, story_outlines, language, intervention_text) -> str`: Constructs the prompt for the Game Master (GM) Agent.
  - `build_story_start_prompt(instance, world, characters) -> str`: Constructs the prompt for the GM to generate the very first scene.
  - `build_character_prompt(character, gm_context, guild_id, location, date, time) -> Tuple[Tuple[str, str]]`: Constructs the prompts for the Character Agent.  Returns:     A tuple containing (system_prompt, user_prompt).

