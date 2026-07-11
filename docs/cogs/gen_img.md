# File: `cogs/gen_img.py`

## Overview
The GenImg cog provides AI-powered image generation capabilities using Google's Gemini API. It enables users to generate high-quality images from text descriptions through a simple Discord interface with support for multiple languages.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `gen_img.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `ImageGenerationCog`
Class managing ImageGenerationCog state and behavior.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.
  - `session` (`Any`): Internal instance state.
  - `tokens` (`Any`): Internal instance state.
  - `client` (`Any`): Internal instance state.
  - `model_id` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any) -> Any`: Performs internal processing logic.
  - `cog_load() -> Any`: Initialize the language manager when the cog is loaded
  - `_get_conversation_history(channel_id: int) -> List[Dict]`: Get the conversation history for a specific channel
  - `_update_conversation_history(channel_id: int, role: str, content: str, images: Optional[List[Image.Image]]) -> Any`: Update the conversation history
  - `_generate_image_logic(prompt: str, guild_id: str, channel_id: int, input_images: Optional[List[Image.Image]], channel: Optional[discord.TextChannel]) -> Dict`: Core image generation logic.
  - `generate_image_command(interaction: discord.Interaction, prompt: str) -> Any`: Performs internal processing logic.
  - `_image_to_base64(image: Image.Image) -> str`: Convert a PIL Image to a base64-encoded string
  - `generate_with_gemini(prompt: str, image_input: List[Image.Image], dialogue_history: List[Dict]) -> tuple[Tuple]`: Generate images using the Gemini API
  - `generate_with_local_model(channel: Any, prompt: str, n_steps: int, message_to_edit: discord.Message, guild_id: str) -> Any`: Generate images using a local model
  - `cog_unload() -> Any`: 清理資源

## Functions

### `setup(bot: Any) -> Any`
Performs internal processing logic.
