# File: `cogs/userdata.py`

## Overview
The UserData cog provides comprehensive personal user data management capabilities, allowing users to save and retrieve their preferences, background information, and interaction rules through an AI-powered memory system. It features intelligent data merging and structured response handling.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `userdata.py`, providing vital integrations within the PigPig bot ecosystem.
User data management cog for Discord bot.

This module provides commands and utilities for managing personalized user data,
including preferences, display names, and interaction rules stored in a database.

## Classes

### `UserDataResponse`
Structured response schema for user data agent.

Attributes:
    procedural_memory: Free-form memory about user preferences and interactions.
    user_background: List of background information about the user.
    display_names: List of display names the user has used.

- **Attributes**:
  - `procedural_memory` (`Optional[str]`): Property holding the procedural_memory state.
  - `user_background` (`Optional[str]`): Property holding the user_background state.
  - `display_names` (`List[str]`): Property holding the display_names state.

### `UserDataCog`
Manages personalized user data for Discord bot interactions.

Provides /memory command group allowing users to save or view bot's
memory about them, such as preferences, nicknames, or interaction rules.

Attributes:
    bot: The Discord bot instance.
    user_manager: Manager for user data persistence.
    lang_manager: Manager for multi-language support.
    logger: Logger instance for this cog.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `user_manager` (`Any`): Internal instance state.
  - `_knowledge_lock` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.
  - `knowledge_storage` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: commands.Bot, user_manager: Optional[SQLiteUserManager]) -> None`: Initializes the UserDataCog.
  - `cog_load() -> None`: Initializes language manager and user manager when cog loads.
  - `_translate(guild_id: str) -> str`: Unified translation method with fallback mechanism.
  - `_get_guild_id_from_context(context: Union[Tuple]) -> str`: Extracts guild_id from various context types.
  - `_extract_json_from_response(response_text: str) -> Optional[Dict[Tuple]]`: Extracts and validates JSON from AI response text.
  - `_validate_user_data_response(data: Dict[Tuple]) -> bool`: Validates that response contains expected user data fields.
  - `_extract_user_id_from_context(context: Union[Tuple]) -> Optional[str]`: Extracts user ID from context (interaction or message).
  - `_read_user_data(user_id: str, context: Union[Tuple]) -> str`: Core logic for reading and formatting user's stored data.
  - `_invoke_ai_merge_agent(existing_data: Optional[UserInfo], new_data: str, user_id: str) -> UserDataResponse`: Invokes AI agent to merge existing and new user data.
  - `_invoke_knowledge_merge_agent(existing_knowledge: Optional[str], new_knowledge: str, target_type: str, category: str) -> str`: Invokes AI agent to merge existing and new guild/channel knowledge.
  - `_save_knowledge_data(target_type: str, target_id: str, content: str, category: str, context: Union[Tuple]) -> str`: Core logic for saving guild/channel knowledge with AI merge.
  - `_clear_knowledge_data(target_type: str, target_id: str) -> str`: Core logic for clearing guild/channel knowledge.
  - `_save_user_data(user_id: str, discord_name: str, user_data: str, context: Union[Tuple], nickname: Optional[str]) -> str`: Core logic for saving user data with AI-assisted merge.
  - `memory_save(interaction: discord.Interaction, preference: str) -> None`: Handles /memory save command to store user preferences.
  - `memory_clear(interaction: discord.Interaction) -> None`: Handles /memory clear command to clear user preferences.
  - `memory_show(interaction: discord.Interaction) -> None`: Handles /memory show command to display stored user preferences.
  - `knowledge_show(interaction: discord.Interaction, scope: app_commands.Choice[str]) -> None`: Handles /knowledge show command to display stored knowledge.
  - `knowledge_save(interaction: discord.Interaction, scope: app_commands.Choice[str], content: str, category: str) -> None`: Handles /knowledge save command to save or update stored knowledge.
  - `knowledge_clear(interaction: discord.Interaction, scope: app_commands.Choice[str]) -> None`: Handles /knowledge clear command to clear stored knowledge.
  - `manage_user_data(context: Union[Tuple], user: Union[Tuple], user_data: str, action: str, message_to_edit: Optional[discord.Message]) -> str`: Dispatcher for managing user data operations.
  - `_clear_user_data(user_id: str, context: Union[Tuple]) -> str`: Core logic for clearing user data.
  - `manage_user_data_message(message: Union[Tuple], user_id: Optional[str], user_data: str, action: str, message_to_edit: Optional[discord.Message]) -> str`: Manages user data triggered from message (for internal tool use).
  - `get_user_statistics() -> Dict[Tuple]`: Retrieves user statistics from user manager.
  - `update_user_activity(user_id: str, discord_name: str, nickname: Optional[str]) -> bool`: Updates user activity status.

## Functions

### `setup(bot: commands.Bot) -> None`
Sets up the UserDataCog.
