# File: `llm/utils/send_message.py`

## Overview
Simplified message sender module for Discord bot GPT responses.

## Classes

No classes defined in this file.

## Functions

### `get_converter(lang: str) -> Optional[opencc.OpenCC]`
Gets appropriate converter based on language.

### `_sanitize_response(text: str) -> str`
Sanitizes response text to prevent accidental Discord mentions.

### `safe_edit_message(message: discord.Message, content: str, max_retries: int) -> bool`
Safely edits a Discord message with retry logic.

### `_safe_send_message(channel: discord.abc.Messageable, content: str, files: Optional[List[discord.File]], max_retries: int) -> discord.Message`
Safely sends a Discord message with retry logic.

### `_get_processing_message(message: discord.Message, lang_manager, message_type: str) -> str`
Gets localized processing message.

### `_process_token_stream(streamer: AsyncIterator, converter: Optional[opencc.OpenCC], current_message: discord.Message, channel: discord.abc.Messageable, message: discord.Message, lang_manager, update_interval: float, tools: Optional[List[Any]], inactivity_timeout: float) -> Tuple[Tuple[str, discord.Message]]`
Processes token stream and updates Discord messages based on time interval.

### `send_message(bot: Any, message_to_edit: Optional[discord.Message], message: discord.Message, streamer: AsyncIterator, update_interval: float, raise_exception: bool, tools: Optional[List[Any]], inactivity_timeout: float) -> str`
Consumes a token stream and updates Discord messages with time-based updates.

