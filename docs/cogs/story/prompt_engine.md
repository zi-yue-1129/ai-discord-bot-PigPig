# File: `cogs/story/prompt_engine.py`

## Overview
This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `prompt_engine.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `StoryPromptEngine`
Builds high-quality prompts for the layered AI agents in the story.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.
  - `system_prompt_manager` (`Any`): Internal instance state.
  - `language_map` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: commands.Bot, system_prompt_manager: SystemPromptManager) -> Any`: Performs internal processing logic.
  - `build_gm_prompt(instance: StoryInstance, world: StoryWorld, characters: List[StoryCharacter], user_input: str, story_outlines: List[str], language: str, intervention_text: Optional[str]) -> str`: Constructs the prompt for the Game Master (GM) Agent.
  - `build_story_start_prompt(instance: StoryInstance, world: StoryWorld, characters: List[StoryCharacter]) -> str`: Constructs the prompt for the GM to generate the very first scene.
  - `_get_fallback_gm_prompt() -> str`: 提供回退的 GM 系統提示詞，當沒有頻道特定的系統提示詞時使用。
  - `build_character_prompt(character: StoryCharacter, gm_context: DialogueContext, guild_id: int, location: str, date: str, time: str) -> Tuple[Tuple]`: Constructs the prompts for the Character Agent.


## Handwritten Context
# Story System - Prompt Engine

**File:** [`cogs/story/prompt_engine.py`](cogs/story/prompt_engine.py)

The `StoryPromptEngine` is a crucial component responsible for dynamically constructing the complex, context-rich prompts that are sent to the AI agents. It tailors the prompts for both the "Director" (GM) and "Actor" (Character) agents.

## `StoryPromptEngine` Class

### `__init__(self, bot, system_prompt_manager)`

Initializes the engine with references to the bot (to access cogs like `LanguageManager`) and the `SystemPromptManager`.

### `async build_gm_prompt(self, ...)`

Constructs the prompt for the Director (Game Master) agent. This is a comprehensive prompt that assembles all necessary information for the AI to make a high-level decision about the story's direction.

*   **Components of the Prompt:**
    1.  **Base Prompt:** It starts with the effective system prompt for the channel, retrieved from the `SystemPromptManager`.
    2.  **Intervention:** If a user has submitted an `/story intervene` command, that text is injected with high priority.
    3.  **Story Outline:** High-level plot outlines generated from previous summaries are included for long-term context.
    4.  **World & Scene Context:** Details about the world, the current location, date, and time are added.
    5.  **Event History:** Summaries of the last few events that occurred in the current location are included.
    6.  **Characters Present:** A list of all characters in the scene, along with their descriptions and current status.
    7.  **Player's Action:** The user's most recent message is appended.
    8.  **Task Definition:** A clear set of instructions explaining the AI's role as the Director and the requirement to output a valid `GMActionPlan` JSON object.
    9.  **Language Instruction:** Specifies the language for the AI to use in its response, based on the server's setting.

### `async build_character_prompt(self, ...)`

Constructs a pair of prompts (system and user) for an Actor (Character) agent. This prompt is more focused, providing the AI with everything it needs to perform as a specific character.

*   **System Prompt (Identity & Core Instructions):**
    *   **Identity:** "You are **Character Name**." Includes the character's background, personality, and traits.
    *   **Core Instructions:** Explains the AI's role as an actor who must follow the Director's guidance and output a valid `CharacterAction` JSON object.
*   **User Prompt (Situational Context & Task):**
    *   **Director's Guidance:** This is the most critical part. It includes the `motivation` and `emotional_state` provided by the Director agent in the `GMActionPlan`.
    *   **Scene Context:** The current location, date, and time.
    *   **Task:** Instructs the AI to perform its action based on the provided context and guidance.

### `_get_fallback_gm_prompt(self)`

Provides a generic, hardcoded system prompt for the GM agent. This is used as a safety measure in case a system prompt cannot be loaded from the `SystemPromptManager`, ensuring the story can always proceed.