# File: `cogs/gen_img.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `ImageGenerationCog`
Core class implementation.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `lang_manager` (`Optional[LanguageManager]`): Attribute holding lang_manager data.
  - `session` (`Any`): Attribute holding session data.
  - `tokens` (`Any`): Attribute holding tokens data.
  - `client` (`Any`): Attribute holding client data.
  - `model_id` (`Any`): Attribute holding model_id data.
  - `conversation_history` (`Dict[Tuple[int, List[Dict]]]`): Attribute holding conversation_history data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(bot) -> Any`: Executes __init__ logic.
  - `cog_load() -> Any`: Initialize the language manager when the cog is loaded
  - `_get_conversation_history(channel_id: int) -> List[Dict]`: Get the conversation history for a specific channel
  - `_update_conversation_history(channel_id: int, role: str, content: str, images: Optional[List[Image.Image]]) -> Any`: Update the conversation history
  - `_generate_image_logic(prompt: str, guild_id: str, channel_id: int, input_images: Optional[List[Image.Image]], channel: Optional[discord.TextChannel]) -> Dict`: Core image generation logic.
  - `generate_image_command(interaction: discord.Interaction, prompt: str) -> Any`: Executes generate_image_command logic.
  - `_image_to_base64(image: Image.Image) -> str`: Convert a PIL Image to a base64-encoded string
  - `generate_with_gemini(prompt: str, image_input: List[Image.Image], dialogue_history: List[Dict]) -> tuple[Tuple[Optional[io.BytesIO], Optional[str]]]`: Generate images using the Gemini API
  - `generate_with_local_model(channel, prompt: str, n_steps: int, message_to_edit: discord.Message, guild_id: str) -> Any`: Generate images using a local model
  - `cog_unload() -> Any`: 清理資源

## Functions

### `setup(bot) -> Any`
Performs setup operations.
