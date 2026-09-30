# File: `cogs/gen_img.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/gen_img.py`.

## Classes

### `ImageGenerationCog`
Class representing ImageGenerationCog.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `lang_manager` (`Optional[LanguageManager]`): Instance attribute lang_manager
  - `session` (`Any`): Instance attribute session
  - `tokens` (`Any`): Instance attribute tokens
  - `client` (`Any`): Instance attribute client
  - `model_id` (`Any`): Instance attribute model_id
  - `conversation_history` (`Dict[int, List[Dict]]`): Instance attribute conversation_history
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `cog_load(self) -> Any`: Initialize the language manager when the cog is loaded
  - `_get_conversation_history(self, channel_id) -> List[Dict]`: Get the conversation history for a specific channel
  - `_update_conversation_history(self, channel_id, role, content, images) -> Any`: Update the conversation history
  - `_generate_image_logic(self, prompt, guild_id, channel_id, input_images, channel) -> Dict`: Core image generation logic.  Returns a dict containing 'content' and/or 'file', or a dict with 'error'.
  - `generate_image_command(self, interaction, prompt) -> Any`: Method generate_image_command.
  - `_image_to_base64(self, image) -> str`: Convert a PIL Image to a base64-encoded string
  - `generate_with_gemini(self, prompt, image_input, dialogue_history) -> tuple[Optional[io.BytesIO], Optional[str]]`: Generate images using the Gemini API
  - `generate_with_local_model(self, channel, prompt, n_steps, message_to_edit, guild_id) -> Any`: Generate images using a local model
  - `cog_unload(self) -> Any`: 清理資源

## Functions

### `setup(bot) -> Any`
Function setup.

