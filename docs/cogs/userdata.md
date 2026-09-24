# File: `cogs/userdata.py`

## Overview
User data management cog for Discord bot.

## Classes

### `UserDataResponse`
Structured response schema for user data agent.

- **Attributes**:
  - `procedural_memory` (`Optional[str]`): Class attribute
  - `user_background` (`Optional[str]`): Class attribute
  - `display_names` (`List[str]`): Class attribute

- **Methods**:
  - None specified.

### `UserDataCog`
Manages personalized user data for Discord bot interactions.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: commands.Bot, user_manager: Optional[SQLiteUserManager]) -> None`: Initializes the UserDataCog.
  - `cog_load() -> None`: Initializes language manager and user manager when cog loads.
  - `_translate(guild_id: str, *path: str, fallback_key: str, **kwargs: Any) -> str`: Unified translation method with fallback mechanism.
  - `_get_guild_id_from_context(context: Union[Tuple[discord.Interaction, discord.Message]]) -> str`: Extracts guild_id from various context types.
  - `_extract_json_from_response(response_text: str) -> Optional[Dict[Tuple[str, Any]]]`: Extracts and validates JSON from AI response text.
  - `_validate_user_data_response(data: Dict[Tuple[str, Any]]) -> bool`: Validates that response contains expected user data fields.
  - `_extract_user_id_from_context(context: Union[Tuple[discord.Interaction, discord.Message]]) -> Optional[str]`: Extracts user ID from context (interaction or message).
  - `_read_user_data(user_id: str, context: Union[Tuple[discord.Interaction, discord.Message]]) -> str`: Core logic for reading and formatting user's stored data.
  - `_invoke_ai_merge_agent(existing_data: Optional[UserInfo], new_data: str, user_id: str) -> UserDataResponse`: Invokes AI agent to merge existing and new user data.
  - `_invoke_knowledge_merge_agent(existing_knowledge: Optional[str], new_knowledge: str, target_type: str, category: str) -> str`: Invokes AI agent to merge existing and new guild/channel knowledge.
  - `_save_knowledge_data(target_type: str, target_id: str, content: str, category: str, context: Union[Tuple[discord.Interaction, discord.Message]]) -> str`: Core logic for saving guild/channel knowledge with AI merge.
  - `_clear_knowledge_data(target_type: str, target_id: str) -> str`: Core logic for clearing guild/channel knowledge.
  - `_save_user_data(user_id: str, discord_name: str, user_data: str, context: Union[Tuple[discord.Interaction, discord.Message]], nickname: Optional[str]) -> str`: Core logic for saving user data with AI-assisted merge.
  - `memory_save(interaction: discord.Interaction, preference: str) -> None`: Handles /memory save command to store user preferences.
  - `memory_clear(interaction: discord.Interaction) -> None`: Handles /memory clear command to clear user preferences.
  - `memory_show(interaction: discord.Interaction) -> None`: Handles /memory show command to display stored user preferences.
  - `knowledge_show(interaction: discord.Interaction, scope: app_commands.Choice[str]) -> None`: Handles /knowledge show command to display stored knowledge.
  - `knowledge_save(interaction: discord.Interaction, scope: app_commands.Choice[str], content: str, category: str) -> None`: Handles /knowledge save command to save or update stored knowledge.
  - `knowledge_clear(interaction: discord.Interaction, scope: app_commands.Choice[str]) -> None`: Handles /knowledge clear command to clear stored knowledge.
  - `manage_user_data(context: Union[Tuple[discord.Interaction, discord.Message]], user: Union[Tuple[discord.User, discord.Member]], user_data: str, action: str, message_to_edit: Optional[discord.Message]) -> str`: Dispatcher for managing user data operations.
  - `_clear_user_data(user_id: str, context: Union[Tuple[discord.Interaction, discord.Message]]) -> str`: Core logic for clearing user data.
  - `manage_user_data_message(message: Union[Tuple[discord.Interaction, discord.Message]], user_id: Optional[str], user_data: str, action: str, message_to_edit: Optional[discord.Message]) -> str`: Manages user data triggered from message (for internal tool use).
  - `get_user_statistics() -> Dict[Tuple[str, Any]]`: Retrieves user statistics from user manager.
  - `update_user_activity(user_id: str, discord_name: str, nickname: Optional[str]) -> bool`: Updates user activity status.

## Functions

### `setup(bot: commands.Bot) -> None`
Sets up the UserDataCog.

