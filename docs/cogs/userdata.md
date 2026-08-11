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
  - `procedural_memory` (`Optional[str]`): Stores data related to procedural_memory.
  - `user_background` (`Optional[str]`): Stores data related to user_background.
  - `display_names` (`List[str]`): Stores data related to display_names.

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
  - `bot` (`Any`): Instance attribute managing bot.
  - `user_manager` (`Any`): Instance attribute managing user_manager.
  - `_knowledge_lock` (`Any`): Instance attribute managing _knowledge_lock.
  - `logger` (`Any`): Instance attribute managing logger.
  - `knowledge_storage` (`Any`): Instance attribute managing knowledge_storage.

- **Methods**:
  - `cog_load() -> None`: Initializes language manager and user manager when cog loads.
  - `memory_save(interaction, preference) -> None`: Handles /memory save command to store user preferences.  Args:     interaction: Discord interaction object.     preference: String data user wants to be remembered.
  - `memory_clear(interaction) -> None`: Handles /memory clear command to clear user preferences.  Args:     interaction: Discord interaction object.
  - `memory_show(interaction) -> None`: Handles /memory show command to display stored user preferences.  Args:     interaction: Discord interaction object.
  - `knowledge_show(interaction, scope) -> None`: Handles /knowledge show command to display stored knowledge.
  - `knowledge_save(interaction, scope, content, category) -> None`: Handles /knowledge save command to save or update stored knowledge.
  - `knowledge_clear(interaction, scope) -> None`: Handles /knowledge clear command to clear stored knowledge.
  - `manage_user_data(context, user, user_data, action, message_to_edit) -> str`: Dispatcher for managing user data operations.  Args:     context: Interaction or message context.     user: Target user object.     user_data: Optional data to save (only used for 'save' action).     action: Either 'read', 'save', or 'clear'.     message_to_edit: Optional message object to edit during processing.      Returns:     Operation result string.
  - `manage_user_data_message(message, user_id, user_data, action, message_to_edit) -> str`: Manages user data triggered from message (for internal tool use).  Args:     message: Triggering Discord message object.     user_id: Optional target user ID.     user_data: Optional data to save.     action: Either 'read' or 'save'.     message_to_edit: Optional message to edit.      Returns:     Operation result string.
  - `get_user_statistics() -> Dict[Tuple[str, Any]]`: Retrieves user statistics from user manager.  Returns:     Dictionary containing statistics, or error message.
  - `update_user_activity(user_id, discord_name, nickname) -> bool`: Updates user activity status.  Args:     user_id: User ID string.     display_name: Optional user display name.      Returns:     True if successful, False otherwise.

## Functions

### `setup(bot) -> None`
Sets up the UserDataCog.

Args:
    bot: The Discord bot instance.

