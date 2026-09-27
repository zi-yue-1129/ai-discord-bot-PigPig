# File: `llm/tools/system_prompt_tools.py`

## Overview
LangChain tool for the bot to modify its own system prompt.

The LLM reads its current personality from the system-prompt context it
already has, generates a merged version, and calls this tool to write it.
Only the write side lives here — no extra LLM call is needed.

## Classes

### `SystemPromptTools`
Container for the bot's self-modification tool.

- **Attributes**:
  - `runtime` (`Any`): Instance attribute for runtime.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(runtime) -> None`: Initialize with the orchestrator runtime context.
  - `get_tools() -> list`: Return the list of self-modification tools.

## Functions

### `check_personality_permission(bot, author, guild, channel, scope) -> Any`
Check whether *author* may modify the personality at *scope*.

### `write_personality(guild_id, channel_id, merged_prompt, scope, bot, user_id) -> str`
Write a merged personality string to the system prompt store.
