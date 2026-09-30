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
  - `runtime` (`Any`): Instance attribute runtime
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `get_tools(self) -> list`: Return the list of self-modification tools.  Returns:     List containing the update_personality StructuredTool.

## Functions

### `check_personality_permission(bot, author, guild, channel, scope) -> str | None`
Check whether *author* may modify the personality at *scope*.  Any scope other than "server" results in a channel-level write in :func:`write_personality`, so it is validated as a channel change.  Args:     bot: The discord.ext.commands.Bot instance.     author: The member requesting the change.     guild: The guild the change applies to.     channel: The channel the change applies to.     scope: "channel" or "server".  Returns:     None if permitted, otherwise a human-readable error string.

### `write_personality(guild_id, channel_id, merged_prompt, scope, bot, user_id) -> str`
Write a merged personality string to the system prompt store.  Args:     guild_id: Discord guild ID string.     channel_id: Discord channel ID string.     merged_prompt: The complete merged system prompt text.     scope: "channel" or "server".     bot: The discord.ext.commands.Bot instance.     user_id: ID of the user requesting the change (for audit).  Returns:     A human-readable confirmation or error string.
