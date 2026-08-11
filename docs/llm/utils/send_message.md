# File: `llm/utils/send_message.py`

## Overview
Simplified message sender module for Discord bot GPT responses.

This module handles message generation with language conversion,
channel-level system prompts, and basic message reply functionality.

## Functions

### `get_converter(lang) -> Optional[opencc.OpenCC]`
Gets appropriate converter based on language.

Args:
    lang: Language code (e.g., 'zh_TW', 'zh_CN', 'en_US', 'ja_JP').

Returns:
    OpenCC converter instance or None if conversion is not needed.

### `safe_edit_message(message, content, max_retries) -> bool`
Safely edits a Discord message with retry logic.

Args:
    message: Discord message to edit.
    content: New content for the message.
    max_retries: Maximum number of retry attempts.

Returns:
    True if message was successfully edited, False if content was empty or other issues.

Raises:
    discord.errors.HTTPException: If all retry attempts fail.

### `send_message(bot, message_to_edit, message, streamer, update_interval, raise_exception, tools, inactivity_timeout) -> str`
Consumes a token stream and updates Discord messages with time-based updates.

This function processes tokens from the stream and updates Discord messages
at regular intervals to avoid rate limiting. When the message grows beyond
the Discord character limit, it creates a new continuation message.

Args:
    bot: Discord bot instance.
    message_to_edit: Optional existing message to edit. If None, creates new.
    message: Original Discord message for context and channel information.
    streamer: Token stream iterator (async or sync).
    update_interval: Time interval (seconds) between message updates.
    raise_exception: If True, raise exception on failure instead of sending error message.

Returns:
    Full message result string.

