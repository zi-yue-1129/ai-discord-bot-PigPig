# File: `llm/tools/user_data.py`

## Overview
User memory management tools for LLM integration.

This module provides LangChain-compatible tools for managing user personal
memory (procedural memory) through the UserDataCog.

## Classes

### `UserMemoryTools`
Container class for user memory management tools.  This class provides tools for a LangChain Agent to manage a user's personal memory (also known as procedural memory). It encapsulates the UserDataCog's functionality, allowing the Agent to read or save specific preferences, facts, or interaction rules that the user has previously asked the bot to remember.  Attributes:     runtime: The orchestrator request containing bot, message, and logger.     logger: Logger instance for this tool.

- **Attributes**:
  - `runtime` (`Any`): Instance attribute runtime
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `_get_bot(self) -> Optional[Any]`: Safely retrieves the bot instance from the runtime.  Returns:     The bot instance if available, None otherwise.
  - `_get_cog(self) -> Optional[UserDataCog]`: Safely retrieves the UserDataCog.  Returns:     The UserDataCog instance if available, None otherwise.
  - `get_tools(self) -> list`: Returns a list of LangChain tools bound to this runtime.  Returns:     A list containing user memory management tools with runtime context.

## Functions

None

