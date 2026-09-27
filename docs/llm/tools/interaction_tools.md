# File: `llm/tools/interaction_tools.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `interaction_tools` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `DiscordInteractionTools`
Tools for advanced Discord interactions (Emojis, Polls, Stickers).

- **Attributes**:
  - `runtime` (`Any`): Instance attribute for runtime.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(runtime) -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `get_tools() -> list`: Handles the `get_tools` functionality. Internally, it interacts with methods like `min` and `sorted`.
