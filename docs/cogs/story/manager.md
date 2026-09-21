# File: `cogs/story/manager.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `StoryManager`
The core manager for story logic. It coordinates the database, state,
and prompt engine to generate story progression based on the v5 layered AI agent architecture.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `cog` (`Any`): Attribute holding cog data.
  - `logger` (`Any`): Attribute holding logger data.
  - `system_prompt_manager` (`Any`): Attribute holding system_prompt_manager data.
  - `_initialized` (`Any`): Attribute holding _initialized data.
  - `db_instances` (`Dict[Tuple[int, StoryDB]]`): Attribute holding db_instances data.
  - `character_db` (`Any`): Attribute holding character_db data.
  - `prompt_engine` (`Any`): Attribute holding prompt_engine data.
  - `state_manager` (`Any`): Attribute holding state_manager data.
  - `language_manager` (`LanguageManager`): Attribute holding language_manager data.
  - `interventions` (`Dict[Tuple[int, str]]`): Attribute holding interventions data.

- **Methods**:
  - `__init__(bot: commands.Bot, cog: commands.Cog, system_prompt_manager: SystemPromptManager) -> Any`: Executes __init__ logic.
  - `_get_db(guild_id: int) -> StoryDB`: Gets or creates a database connection for a specific guild.
  - `_extract_structured_response(response: Any, expected_model: Type[T], context: str) -> Optional[T]`: Unified extractor for structured agent responses.
  - `initialize() -> Any`: Initializes the StoryManager and its components.
  - `add_intervention(channel_id: int, text: str) -> Any`: Stores an intervention for a specific channel.
  - `intervene(interaction: discord.Interaction) -> Any`: Opens a modal for the user to provide an OOC intervention.
  - `_update_relationships(db: StoryDB, story_id: int, updates: List[RelationshipUpdate]) -> Any`: Updates player-NPC relationships based on the GM plan.
  - `_record_event(db: StoryDB, world: StoryWorld, instance: StoryInstance, gm_plan: GMActionPlan, final_content: str) -> Any`: Creates and records an event in the world state.
  - `_send_story_response(channel: discord.TextChannel, character: Optional[StoryCharacter], story_instance: StoryInstance, content: str | CharacterAction) -> Any`: Constructs and sends the story response as an embed, using a webhook if available.
  - `process_story_message(message: discord.Message) -> Any`: Processes a message from a story channel using the v5 layered agent architecture.
  - `_find_speaking_character(speaker_name: Optional[str], characters: List[StoryCharacter], channel: discord.abc.Messageable) -> Optional[StoryCharacter]`: Unified character lookup logic, supports multiple matching methods.
  - `_generate_and_save_summary(story_instance: StoryInstance) -> Any`: Generates a summary of the last 20-40 messages and saves it.
  - `_generate_and_save_outline(story_instance: StoryInstance) -> Any`: Generates a high-level outline from the last 10 summaries and saves it.
  - `start_story(interaction: discord.Interaction, world_name: str, character_ids: List[str], use_narrator: bool, initial_date: Optional[str], initial_time: Optional[str], initial_location: str) -> Any`: Handles the logic of starting a new story, creating the instance,
  - `generate_first_scene(interaction: discord.Interaction, story_instance: StoryInstance) -> Any`: Generates the introductory scene for a new story using the v5 architecture.

## Functions

No top-level functions defined.
