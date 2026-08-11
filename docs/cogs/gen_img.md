# File: `cogs/gen_img.py`

## Overview
The GenImg cog provides AI-powered image generation capabilities using Google's Gemini API. It enables users to generate high-quality images from text descriptions through a simple Discord interface with support for multiple languages.

## Classes

### `ImageGenerationCog`
Manages the state and core operations for ImageGenerationCog.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `session` (`Any`): Instance attribute managing session.
  - `tokens` (`Any`): Instance attribute managing tokens.
  - `client` (`Any`): Instance attribute managing client.
  - `model_id` (`Any`): Instance attribute managing model_id.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `cog_load() -> Any`: Initialize the language manager when the cog is loaded
  - `generate_image_command(interaction, prompt) -> Any`: Executes logic for generate_image_command.
  - `generate_with_gemini(prompt, image_input, dialogue_history) -> tuple[Tuple[Optional[io.BytesIO], Optional[str]]]`: Generate images using the Gemini API
  - `generate_with_local_model(channel, prompt, n_steps, message_to_edit, guild_id) -> Any`: Generate images using a local model
  - `cog_unload() -> Any`: 清理資源

## Functions

### `setup(bot) -> Any`
Performs setup operations.

