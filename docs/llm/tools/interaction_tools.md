# File: `llm/tools/interaction_tools.py`

## Overview
The `DiscordInteractionTools` class provides advanced interaction capabilities beyond simple text responses. These tools allow the LLM to manage reactions, use custom server emojis, send stickers, change its local identity, and manipulate the conversational flow with timing and message retraction.

## Classes

### `DiscordInteractionTools`
Tools for advanced Discord interactions (Emojis, Polls, Stickers).

- **Attributes**:
  - `runtime` (`Any`): Instance attribute managing runtime.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `get_tools() -> list`: Executes logic for get_tools.

