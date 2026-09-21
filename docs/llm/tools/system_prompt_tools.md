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
  - `runtime` (`Any`): Attribute holding runtime data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> None`: Initialize with the orchestrator runtime context.
  - `get_tools() -> list`: Return the list of self-modification tools.

## Functions

### `check_personality_permission(bot: Any, author: Any, guild: Any, channel: Any, scope: str) -> str | None`
Check whether *author* may modify the personality at *scope*.

Any scope other than "server" results in a channel-level write in
:func:`write_personality`, so it is validated as a channel change.

Args:
    bot: The discord.ext.commands.Bot instance.
    author: The member requesting the change.
    guild: The guild the change applies to.
    channel: The channel the change applies to.
    scope: "channel" or "server".

Returns:
    None if permitted, otherwise a human-readable error string.

### `write_personality(guild_id: str, channel_id: str, merged_prompt: str, scope: str, bot: Any, user_id: str) -> str`
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
