# File: `cogs/userdata.py`

## Overview
User data management cog for Discord bot.

This module provides commands and utilities for managing personalized user data,
including preferences, display names, and interaction rules stored in a database.

## Classes

### `UserDataResponse`
Structured response schema for user data agent.  Attributes:     procedural_memory: Free-form memory about user preferences and interactions.     user_background: List of background information about the user.     display_names: List of display names the user has used.

- **Attributes**:
  - `procedural_memory` (`Optional[str]`): Attribute procedural_memory
  - `user_background` (`Optional[str]`): Attribute user_background
  - `display_names` (`List[str]`): Attribute display_names

- **Methods**:
  - None

### `UserDataCog`
Manages personalized user data for Discord bot interactions.  Provides /memory command group allowing users to save or view bot's memory about them, such as preferences, nicknames, or interaction rules.  Attributes:     bot: The Discord bot instance.     user_manager: Manager for user data persistence.     lang_manager: Manager for multi-language support.     logger: Logger instance for this cog.

- **Attributes**:
  - `memory_group` (`Any`): Attribute memory_group
  - `knowledge_group` (`Any`): Attribute knowledge_group
  - `bot` (`Any`): Instance attribute bot
  - `user_manager` (`Any`): Instance attribute user_manager
  - `_knowledge_lock` (`Any`): Instance attribute _knowledge_lock
  - `lang_manager` (`Optional[LanguageManager]`): Instance attribute lang_manager
  - `logger` (`Any`): Instance attribute logger
  - `knowledge_storage` (`Any`): Instance attribute knowledge_storage

- **Methods**:
  - `cog_load(self) -> None`: Initializes language manager and user manager when cog loads.
  - `_translate(self, guild_id, *path, **kwargs) -> str`: Unified translation method with fallback mechanism.  Args:     guild_id: Server ID for determining language.     *path: Path in translation file.     fallback_key: Fallback key in FALLBACK_TRANSLATIONS.     **kwargs: Parameters for formatting translation string.      Returns:     Translated string, or fallback if translation fails.
  - `_get_guild_id_from_context(self, context) -> str`: Extracts guild_id from various context types.  Args:     context: Discord interaction or message object.      Returns:     Guild ID string, or empty string if not found.
  - `_extract_json_from_response(self, response_text) -> Optional[Dict[str, Any]]`: Extracts and validates JSON from AI response text.  Attempts multiple strategies to extract valid JSON: 1. Direct JSON parsing 2. Extracting from code fences (```json ... ```) 3. Finding first {...} span  Args:     response_text: Raw text response from AI.      Returns:     Parsed JSON dictionary or None if extraction fails.
  - `_validate_user_data_response(self, data) -> bool`: Validates that response contains expected user data fields.  Args:     data: Dictionary to validate.      Returns:     True if valid, False otherwise.
  - `_extract_user_id_from_context(self, context) -> Optional[str]`: Extracts user ID from context (interaction or message).  Args:     context: Discord interaction or message object.      Returns:     User ID string or None if not found.
  - `_read_user_data(self, user_id, context) -> str`: Core logic for reading and formatting user's stored data.  Args:     user_id: Target user ID to read data for.     context: Discord context for guild ID and fallback user.      Returns:     Formatted string with user data or error message.
  - `_invoke_ai_merge_agent(self, existing_data, new_data, user_id) -> UserDataResponse`: Invokes AI agent to merge existing and new user data.
  - `_invoke_knowledge_merge_agent(self, existing_knowledge, new_knowledge, target_type, category) -> str`: Invokes AI agent to merge existing and new guild/channel knowledge.
  - `_save_knowledge_data(self, target_type, target_id, content, category, context) -> str`: Core logic for saving guild/channel knowledge with AI merge.
  - `_clear_knowledge_data(self, target_type, target_id) -> str`: Core logic for clearing guild/channel knowledge.
  - `_save_user_data(self, user_id, discord_name, user_data, context, nickname) -> str`: Core logic for saving user data with AI-assisted merge.  Args:     user_id: Target user ID.     display_name: User's display name.     user_data: New data to save.     context: Discord context for guild ID.      Returns:     Success or error message string.
  - `memory_save(self, interaction, preference) -> None`: Handles /memory save command to store user preferences.  Args:     interaction: Discord interaction object.     preference: String data user wants to be remembered.
  - `memory_clear(self, interaction) -> None`: Handles /memory clear command to clear user preferences.  Args:     interaction: Discord interaction object.
  - `memory_show(self, interaction) -> None`: Handles /memory show command to display stored user preferences.  Args:     interaction: Discord interaction object.
  - `knowledge_show(self, interaction, scope) -> None`: Handles /knowledge show command to display stored knowledge.
  - `knowledge_save(self, interaction, scope, content, category) -> None`: Handles /knowledge save command to save or update stored knowledge.
  - `knowledge_clear(self, interaction, scope) -> None`: Handles /knowledge clear command to clear stored knowledge.
  - `manage_user_data(self, context, user, user_data, action, message_to_edit) -> str`: Dispatcher for managing user data operations.  Args:     context: Interaction or message context.     user: Target user object.     user_data: Optional data to save (only used for 'save' action).     action: Either 'read', 'save', or 'clear'.     message_to_edit: Optional message object to edit during processing.      Returns:     Operation result string.
  - `_clear_user_data(self, user_id, context) -> str`: Core logic for clearing user data.  Args:     user_id: Target user ID to clear data for.     context: Discord context for guild ID.  Returns:     Success or error message string.
  - `manage_user_data_message(self, message, user_id, user_data, action, message_to_edit) -> str`: Manages user data triggered from message (for internal tool use).  Args:     message: Triggering Discord message object.     user_id: Optional target user ID.     user_data: Optional data to save.     action: Either 'read' or 'save'.     message_to_edit: Optional message to edit.      Returns:     Operation result string.
  - `get_user_statistics(self) -> Dict[str, Any]`: Retrieves user statistics from user manager.  Returns:     Dictionary containing statistics, or error message.
  - `update_user_activity(self, user_id, discord_name, nickname) -> bool`: Updates user activity status.  Args:     user_id: User ID string.     display_name: Optional user display name.      Returns:     True if successful, False otherwise.

## Functions

### `setup(bot) -> None`
Sets up the UserDataCog.  Args:     bot: The Discord bot instance.

