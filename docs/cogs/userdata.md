# File: `cogs/userdata.py`

## Overview
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
  - `procedural_memory` (`Optional[...]`): Class attribute representing procedural_memory.
  - `user_background` (`Optional[...]`): Class attribute representing user_background.
  - `display_names` (`List[...]`): Class attribute representing display_names.

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
  - `memory_group` (`Any`): Class attribute representing memory_group.
  - `knowledge_group` (`Any`): Class attribute representing knowledge_group.
  - `bot` (`Any`): Instance attribute for bot.
  - `user_manager` (`Any`): Instance attribute for user_manager.
  - `_knowledge_lock` (`Any`): Instance attribute for _knowledge_lock.
  - `lang_manager` (`Optional[...]`): Instance attribute for lang_manager.
  - `logger` (`Any`): Instance attribute for logger.
  - `knowledge_storage` (`Any`): Instance attribute for knowledge_storage.

- **Methods**:
  - `__init__(bot, user_manager) -> None`: Initializes the UserDataCog.
  - `cog_load() -> None`: Initializes language manager and user manager when cog loads.
  - `_translate(guild_id, *path, **kwargs) -> str`: Unified translation method with fallback mechanism.
  - `_get_guild_id_from_context(context) -> str`: Extracts guild_id from various context types.
  - `_extract_json_from_response(response_text) -> Optional[...]`: Extracts and validates JSON from AI response text.
  - `_validate_user_data_response(data) -> bool`: Validates that response contains expected user data fields.
  - `_extract_user_id_from_context(context) -> Optional[...]`: Extracts user ID from context (interaction or message).
  - `_read_user_data(user_id, context) -> str`: Core logic for reading and formatting user's stored data.
  - `_invoke_ai_merge_agent(existing_data, new_data, user_id) -> UserDataResponse`: Invokes AI agent to merge existing and new user data.
  - `_invoke_knowledge_merge_agent(existing_knowledge, new_knowledge, target_type, category) -> str`: Invokes AI agent to merge existing and new guild/channel knowledge.
  - `_save_knowledge_data(target_type, target_id, content, category, context) -> str`: Core logic for saving guild/channel knowledge with AI merge.
  - `_clear_knowledge_data(target_type, target_id) -> str`: Core logic for clearing guild/channel knowledge.
  - `_save_user_data(user_id, discord_name, user_data, context, nickname) -> str`: Core logic for saving user data with AI-assisted merge.
  - `memory_save(interaction, preference) -> None`: Handles /memory save command to store user preferences.
  - `memory_clear(interaction) -> None`: Handles /memory clear command to clear user preferences.
  - `memory_show(interaction) -> None`: Handles /memory show command to display stored user preferences.
  - `knowledge_show(interaction, scope) -> None`: Handles /knowledge show command to display stored knowledge.
  - `knowledge_save(interaction, scope, content, category) -> None`: Handles /knowledge save command to save or update stored knowledge.
  - `knowledge_clear(interaction, scope) -> None`: Handles /knowledge clear command to clear stored knowledge.
  - `manage_user_data(context, user, user_data, action, message_to_edit) -> str`: Dispatcher for managing user data operations.
  - `_clear_user_data(user_id, context) -> str`: Core logic for clearing user data.
  - `manage_user_data_message(message, user_id, user_data, action, message_to_edit) -> str`: Manages user data triggered from message (for internal tool use).
  - `get_user_statistics() -> Dict[...]`: Retrieves user statistics from user manager.
  - `update_user_activity(user_id, discord_name, nickname) -> bool`: Updates user activity status.

## Functions

### `setup(bot) -> None`
Sets up the UserDataCog.
