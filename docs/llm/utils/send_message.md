# File: `llm/utils/send_message.py`

## Overview
Simplified message sender module for Discord bot GPT responses.

This module handles message generation with language conversion,
channel-level system prompts, and basic message reply functionality.

## Functions

### `get_converter(lang) -> Optional[...]`
Gets appropriate converter based on language.

### `_sanitize_response(text) -> str`
Sanitizes response text to prevent accidental Discord mentions.

### `safe_edit_message(message, content, max_retries) -> bool`
Safely edits a Discord message with retry logic.

### `_safe_send_message(channel, content, files, max_retries) -> discord.Message`
Safely sends a Discord message with retry logic.

### `_get_processing_message(message, lang_manager, message_type) -> str`
Gets localized processing message.

### `_process_token_stream(streamer, converter, current_message, channel, message, lang_manager, update_interval, tools, inactivity_timeout) -> Tuple[...]`
Processes token stream and updates Discord messages based on time interval.

### `send_message(bot, message_to_edit, message, streamer, update_interval, raise_exception, tools, inactivity_timeout) -> str`
Consumes a token stream and updates Discord messages with time-based updates.
