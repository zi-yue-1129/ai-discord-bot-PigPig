# File: `cogs/story/prompt_engine.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `prompt_engine` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `StoryPromptEngine`
Builds high-quality prompts for the layered AI agents in the story.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `logger` (`Any`): Instance attribute for logger.
  - `system_prompt_manager` (`Any`): Instance attribute for system_prompt_manager.
  - `language_manager` (`Optional[...]`): Instance attribute for language_manager.
  - `language_map` (`Any`): Instance attribute for language_map.

- **Methods**:
  - `__init__(bot, system_prompt_manager) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `get_cog`.
  - `build_gm_prompt(instance, world, characters, user_input, story_outlines, language, intervention_text) -> str`: Constructs the prompt for the Game Master (GM) Agent.
  - `build_story_start_prompt(instance, world, characters) -> str`: Constructs the prompt for the GM to generate the very first scene.
  - `_get_fallback_gm_prompt() -> str`: 提供回退的 GM 系統提示詞，當沒有頻道特定的系統提示詞時使用。
  - `build_character_prompt(character, gm_context, guild_id, location, date, time) -> Tuple[...]`: Constructs the prompts for the Character Agent.
