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
  - `runtime` (`Any`): Instance attribute managing runtime.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `get_tools() -> list`: Return the list of self-modification tools.  Returns:     List containing the update_personality StructuredTool.

## Functions

### `write_personality(guild_id, channel_id, merged_prompt, scope, bot, user_id) -> str`
Write a merged personality string to the system prompt store.

Args:
    guild_id: Discord guild ID string.
    channel_id: Discord channel ID string.
    merged_prompt: The complete merged system prompt text.
    scope: "channel" or "server".
    bot: The discord.ext.commands.Bot instance.
    user_id: ID of the user requesting the change (for audit).

Returns:
    A human-readable confirmation or error string.
