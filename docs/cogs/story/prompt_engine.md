# File: `cogs/story/prompt_engine.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/story/prompt_engine.py`.

## Classes

### `StoryPromptEngine`
Builds high-quality prompts for the layered AI agents in the story.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `logger` (`Any`): Instance attribute logger
  - `system_prompt_manager` (`Any`): Instance attribute system_prompt_manager
  - `language_manager` (`Optional[LanguageManager]`): Instance attribute language_manager
  - `language_map` (`Any`): Instance attribute language_map

- **Methods**:
  - `build_gm_prompt(self, instance, world, characters, user_input, story_outlines, language, intervention_text) -> str`: Constructs the prompt for the Game Master (GM) Agent.
  - `build_story_start_prompt(self, instance, world, characters) -> str`: Constructs the prompt for the GM to generate the very first scene.
  - `_get_fallback_gm_prompt(self) -> str`: 提供回退的 GM 系統提示詞，當沒有頻道特定的系統提示詞時使用。 這個提示詞旨在讓 AI 理解其在「導演-演員」架構中的角色。  Returns:     一個符合 v5 架構的通用 GM/導演系統提示詞。
  - `build_character_prompt(self, character, gm_context, guild_id, location, date, time) -> Tuple[str, str]`: Constructs the prompts for the Character Agent.  Returns:     A tuple containing (system_prompt, user_prompt).

## Functions

None

