# File: `cogs/story/prompt_engine.py`

## Overview
Core file handling responsibilities within the `cogs/story` subsystem.

## Classes

### `StoryPromptEngine`
Builds high-quality prompts for the layered AI agents in the story.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: commands.Bot, system_prompt_manager: str) -> Any`: No description provided.
  - `build_gm_prompt(instance: StoryInstance, world: StoryWorld, characters: List[StoryCharacter], user_input: str, story_outlines: List[str], language: str, intervention_text: Optional[str]) -> str`: Constructs the prompt for the Game Master (GM) Agent.
  - `build_story_start_prompt(instance: StoryInstance, world: StoryWorld, characters: List[StoryCharacter]) -> str`: Constructs the prompt for the GM to generate the very first scene.
  - `_get_fallback_gm_prompt() -> str`: 提供回退的 GM 系統提示詞，當沒有頻道特定的系統提示詞時使用。
  - `build_character_prompt(character: StoryCharacter, gm_context: str, guild_id: int, location: str, date: str, time: str) -> Tuple[Tuple[str, str]]`: Constructs the prompts for the Character Agent.

## Functions

No module-level functions defined in this file.

