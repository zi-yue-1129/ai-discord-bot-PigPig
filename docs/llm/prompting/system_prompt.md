# File: `llm/prompting/system_prompt.py`

## Overview
The `system_prompt.py` module provides high-level functions for retrieving system prompts with sophisticated fallback hierarchy and three-tier inheritance. It integrates channel-level, server-level, and YAML-based prompts with automatic fallback mechanisms.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `system_prompt.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

## Functions

### `get_channel_system_prompt(channel_id: str, guild_id: str, bot_id: str, message: Optional[discord.Message]) -> str`
Gets channel-specific system prompt with three-tier inheritance.

### `get_system_prompt(bot_id: str, message: Optional[discord.Message]) -> str`
Gets system prompt with fallback hierarchy.
