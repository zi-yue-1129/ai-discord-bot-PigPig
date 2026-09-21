# File: `llm/prompting/system_prompt.py`

## Overview
This file is part of the llm subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

No classes defined.

## Functions

### `get_channel_system_prompt(channel_id: str, guild_id: str, bot_id: str, message: Optional[discord.Message]) -> str`
Gets channel-specific system prompt with three-tier inheritance.

Integrates three-tier inheritance: YAML base + server level + channel level.

Args:
    channel_id: Channel ID.
    guild_id: Server/guild ID.
    bot_id: Discord bot ID.
    message: Discord message object (for language detection).

Returns:
    Complete system prompt string with three-tier inheritance.

### `get_system_prompt(bot_id: str, message: Optional[discord.Message]) -> str`
Gets system prompt with fallback hierarchy.

Priority order:
1. Channel-specific system prompt (if exists and valid)
2. Server-level system prompt (if exists and valid)
3. YAML global default prompt
4. Hardcoded fallback prompt

Args:
    bot_id: Discord bot ID.
    message: Discord message object (for language detection and channel info).

Returns:
    Complete system prompt string.
