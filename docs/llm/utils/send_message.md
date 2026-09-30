# File: `llm/utils/send_message.py`

## Overview
Simplified message sender module for Discord bot GPT responses.

This module handles message generation with language conversion,
channel-level system prompts, and basic message reply functionality.

## Classes

None

## Functions

### `get_converter(lang) -> Optional[opencc.OpenCC]`
Gets appropriate converter based on language.  Args:     lang: Language code (e.g., 'zh_TW', 'zh_CN', 'en_US', 'ja_JP').  Returns:     OpenCC converter instance or None if conversion is not needed.

### `_sanitize_response(text) -> str`
Sanitizes response text to prevent accidental Discord mentions.  Args:     text: Text content to sanitize.  Returns:     Sanitized safe text with @everyone and @here replaced.

### `safe_edit_message(message, content, max_retries) -> bool`
Safely edits a Discord message with retry logic.  Args:     message: Discord message to edit.     content: New content for the message.     max_retries: Maximum number of retry attempts.      Returns:     True if message was successfully edited, False if content was empty or other issues.      Raises:     discord.errors.HTTPException: If all retry attempts fail.

### `_safe_send_message(channel, content, files, max_retries) -> discord.Message`
Safely sends a Discord message with retry logic.  Args:     channel: Discord channel to send message to.     content: Message content.     files: Optional list of files to attach.     max_retries: Maximum number of retry attempts.  Returns:     Sent Discord message.      Raises:     discord.errors.HTTPException: If all retry attempts fail.     ValueError: If content is empty after sanitization.

### `_get_processing_message(message, lang_manager, message_type) -> str`
Gets localized processing message.  Args:     message: Discord message containing guild information.     lang_manager: Language manager instance for translations.     message_type: Type of processing message ('processing' or 'continuation').      Returns:     Localized processing message string.

### `_process_token_stream(streamer, converter, current_message, channel, message, lang_manager, update_interval, tools, inactivity_timeout) -> Tuple[str, discord.Message]`
Processes token stream and updates Discord messages based on time interval.  Args:     streamer: Token stream (async or sync iterator).     converter: OpenCC converter for language conversion.     current_message: Current Discord message being edited.     channel: Discord channel for sending messages.     message: Original Discord message for context.     lang_manager: Language manager for translations.     update_interval: Time interval (seconds) between message updates.     tools: Optional tools list.     inactivity_timeout: Max seconds to wait between tokens before raising TimeoutError.      Returns:     Tuple of (full message result with markers, final Discord message).

### `send_message(bot, message_to_edit, message, streamer, update_interval, raise_exception, tools, inactivity_timeout) -> str`
Consumes a token stream and updates Discord messages with time-based updates.  This function processes tokens from the stream and updates Discord messages at regular intervals to avoid rate limiting. When the message grows beyond the Discord character limit, it creates a new continuation message.  Args:     bot: Discord bot instance.     message_to_edit: Optional existing message to edit. If None, creates new.     message: Original Discord message for context and channel information.     streamer: Token stream iterator (async or sync).     update_interval: Time interval (seconds) between message updates.     raise_exception: If True, raise exception on failure instead of sending error message.      Returns:     Full message result string.

