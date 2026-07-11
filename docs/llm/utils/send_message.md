# File: `llm/utils/send_message.py`

## Overview
The `send_message.py` module provides a sophisticated Discord message handling system for LLM responses. It handles language conversion, streaming responses, message editing, and comprehensive error recovery for Discord bot interactions.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `send_message.py`, providing vital integrations within the PigPig bot ecosystem.
Simplified message sender module for Discord bot GPT responses.

This module handles message generation with language conversion,
channel-level system prompts, and basic message reply functionality.

## Classes

## Functions

### `get_converter(lang: str) -> Optional[opencc.OpenCC]`
Gets appropriate converter based on language.

### `_sanitize_response(text: str) -> str`
Sanitizes response text to prevent accidental Discord mentions.

### `safe_edit_message(message: discord.Message, content: str, max_retries: int) -> bool`
Safely edits a Discord message with retry logic.

### `_safe_send_message(channel: discord.abc.Messageable, content: str, files: Optional[List[discord.File]], max_retries: int) -> discord.Message`
Safely sends a Discord message with retry logic.

### `_get_processing_message(message: discord.Message, lang_manager: Any, message_type: str) -> str`
Gets localized processing message.

### `_process_token_stream(streamer: AsyncIterator, converter: Optional[opencc.OpenCC], current_message: discord.Message, channel: discord.abc.Messageable, message: discord.Message, lang_manager: Any, update_interval: float, tools: Optional[List[Any]], inactivity_timeout: float) -> Tuple[Tuple]`
Processes token stream and updates Discord messages based on time interval.

### `send_message(bot: Any, message_to_edit: Optional[discord.Message], message: discord.Message, streamer: AsyncIterator, update_interval: float, raise_exception: bool, tools: Optional[List[Any]], inactivity_timeout: float) -> str`
Consumes a token stream and updates Discord messages with time-based updates.
