# File: `cogs/gen_img.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `gen_img` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `ImageGenerationCog`
Represents the `ImageGenerationCog` class in the system.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `lang_manager` (`Optional[...]`): Instance attribute for lang_manager.
  - `session` (`Any`): Instance attribute for session.
  - `tokens` (`Any`): Instance attribute for tokens.
  - `client` (`Any`): Instance attribute for client.
  - `model_id` (`Any`): Instance attribute for model_id.
  - `conversation_history` (`Dict[...]`): Instance attribute for conversation_history.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(bot) -> Any`: Handles the `__init__` functionality. Internally, it interacts with methods like `ClientSession` and `Client`.
  - `cog_load() -> Any`: Initialize the language manager when the cog is loaded
  - `_get_conversation_history(channel_id) -> List[...]`: Get the conversation history for a specific channel
  - `_update_conversation_history(channel_id, role, content, images) -> Any`: Update the conversation history
  - `_generate_image_logic(prompt, guild_id, channel_id, input_images, channel) -> Dict`: Core image generation logic.
  - `generate_image_command(interaction, prompt) -> Any`: Handles the `generate_image_command` functionality. Internally, it interacts with methods like `command` and `describe`.
  - `_image_to_base64(image) -> str`: Convert a PIL Image to a base64-encoded string
  - `generate_with_gemini(prompt, image_input, dialogue_history) -> tuple[...]`: Generate images using the Gemini API
  - `generate_with_local_model(channel, prompt, n_steps, message_to_edit, guild_id) -> Any`: Generate images using a local model
  - `cog_unload() -> Any`: 清理資源

## Functions

### `setup(bot) -> Any`
Provides `setup` functionality. Internally, it interacts with methods like `add_cog` and `ImageGenerationCog`.
