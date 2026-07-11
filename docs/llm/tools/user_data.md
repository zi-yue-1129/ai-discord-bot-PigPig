# File: `llm/tools/user_data.py`

## Overview
The `UserMemoryTools` class provides LangChain-compatible tools for managing user personal memory (procedural memory) through the UserDataCog. It enables agents to read and save user preferences, facts, and interaction rules that users have previously asked the bot to remember.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `user_data.py`, providing vital integrations within the PigPig bot ecosystem.
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
  - `runtime` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> Any`: Initializes UserMemoryTools with runtime context.
  - `_get_bot() -> Optional[Any]`: Safely retrieves the bot instance from the runtime.
  - `_get_cog() -> Optional[UserDataCog]`: Safely retrieves the UserDataCog.
  - `get_tools() -> list`: Returns a list of LangChain tools bound to this runtime.
