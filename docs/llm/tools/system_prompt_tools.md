# File: `llm/tools/system_prompt_tools.py`

## Overview
LangChain tool for the bot to modify its own system prompt.

## Classes

### `SystemPromptTools`
Container for the bot's self-modification tool.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(runtime: str) -> None`: Initialize with the orchestrator runtime context.
  - `get_tools() -> list`: Return the list of self-modification tools.

## Functions

### `check_personality_permission(bot: Any, author: Any, guild: Any, channel: Any, scope: str) -> str | None`
Check whether *author* may modify the personality at *scope*.

### `write_personality(guild_id: str, channel_id: str, merged_prompt: str, scope: str, bot: Any, user_id: str) -> str`
Write a merged personality string to the system prompt store.
