# File: `llm/prompting/system_prompt.py`

## Overview
Core file handling responsibilities within the `llm/prompting` subsystem.

## Classes

No classes defined in this file.

## Functions

### `get_channel_system_prompt(channel_id: str, guild_id: str, bot_id: str, message: Optional[discord.Message]) -> str`
Gets channel-specific system prompt with three-tier inheritance.

### `get_system_prompt(bot_id: str, message: Optional[discord.Message]) -> str`
Gets system prompt with fallback hierarchy.

