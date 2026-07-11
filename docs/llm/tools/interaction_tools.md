# File: `llm/tools/interaction_tools.py`

## Overview
The `DiscordInteractionTools` class provides advanced interaction capabilities beyond simple text responses. These tools allow the LLM to manage reactions, use custom server emojis, send stickers, change its local identity, and manipulate the conversational flow with timing and message retraction.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `interaction_tools.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `DiscordInteractionTools`
Tools for advanced Discord interactions (Emojis, Polls, Stickers).

- **Attributes**:
  - `runtime` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> Any`: Performs internal processing logic.
  - `get_tools() -> list`: Performs internal processing logic.
