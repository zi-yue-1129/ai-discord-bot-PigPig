# File: `llm/prompting/system_prompt.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `system_prompt` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Functions

### `get_channel_system_prompt(channel_id, guild_id, bot_id, message) -> str`
Gets channel-specific system prompt with three-tier inheritance.

### `get_system_prompt(bot_id, message) -> str`
Gets system prompt with fallback hierarchy.
