# File: `llm/tools/system_prompt_tools.py`

## Overview
This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `system_prompt_tools.py`, providing vital integrations within the PigPig bot ecosystem.
LangChain tool for the bot to modify its own system prompt.

The LLM reads its current personality from the system-prompt context it
already has, generates a merged version, and calls this tool to write it.
Only the write side lives here — no extra LLM call is needed.

## Classes

### `SystemPromptTools`
Container for the bot's self-modification tool.

- **Attributes**:
  - `runtime` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> None`: Initialize with the orchestrator runtime context.
  - `get_tools() -> list`: Return the list of self-modification tools.

## Functions

### `write_personality(guild_id: str, channel_id: str, merged_prompt: str, scope: str, bot: Any, user_id: str) -> str`
Write a merged personality string to the system prompt store.
