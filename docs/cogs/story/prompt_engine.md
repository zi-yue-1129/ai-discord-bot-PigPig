# File: `cogs/story/prompt_engine.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `StoryPromptEngine`
Builds high-quality prompts for the layered AI agents in the story.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `logger` (`Any`): Attribute holding logger data.
  - `system_prompt_manager` (`Any`): Attribute holding system_prompt_manager data.
  - `language_manager` (`Optional[LanguageManager]`): Attribute holding language_manager data.
  - `language_map` (`Any`): Attribute holding language_map data.

- **Methods**:
  - `__init__(bot: commands.Bot, system_prompt_manager: SystemPromptManager) -> Any`: Executes __init__ logic.
  - `build_gm_prompt(instance: StoryInstance, world: StoryWorld, characters: List[StoryCharacter], user_input: str, story_outlines: List[str], language: str, intervention_text: Optional[str]) -> str`: Constructs the prompt for the Game Master (GM) Agent.
  - `build_story_start_prompt(instance: StoryInstance, world: StoryWorld, characters: List[StoryCharacter]) -> str`: Constructs the prompt for the GM to generate the very first scene.
  - `_get_fallback_gm_prompt() -> str`: 提供回退的 GM 系統提示詞，當沒有頻道特定的系統提示詞時使用。
  - `build_character_prompt(character: StoryCharacter, gm_context: DialogueContext, guild_id: int, location: str, date: str, time: str) -> Tuple[Tuple[str, str]]`: Constructs the prompts for the Character Agent.

## Functions

No top-level functions defined.
