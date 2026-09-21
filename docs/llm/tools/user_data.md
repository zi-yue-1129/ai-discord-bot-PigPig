# File: `llm/tools/user_data.py`

## Overview
User memory management tools for LLM integration.

This module provides LangChain-compatible tools for managing user personal
memory (procedural memory) through the UserDataCog.

## Classes

### `UserMemoryTools`
Container class for user memory management tools.

This class provides tools for a LangChain Agent to manage a user's
personal memory (also known as procedural memory). It encapsulates
the UserDataCog's functionality, allowing the Agent to read or save
specific preferences, facts, or interaction rules that the user has
previously asked the bot to remember.

Attributes:
    runtime: The orchestrator request containing bot, message, and logger.
    logger: Logger instance for this tool.

- **Attributes**:
  - `runtime` (`Any`): Attribute holding runtime data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> Any`: Initializes UserMemoryTools with runtime context.
  - `_get_bot() -> Optional[Any]`: Safely retrieves the bot instance from the runtime.
  - `_get_cog() -> Optional[UserDataCog]`: Safely retrieves the UserDataCog.
  - `get_tools() -> list`: Returns a list of LangChain tools bound to this runtime.

## Functions

No top-level functions defined.
