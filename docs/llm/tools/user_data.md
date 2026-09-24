# File: `llm/tools/user_data.py`

## Overview
User memory management tools for LLM integration.

## Classes

### `UserMemoryTools`
Container class for user memory management tools.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(runtime: str) -> Any`: Initializes UserMemoryTools with runtime context.
  - `_get_bot() -> Optional[Any]`: Safely retrieves the bot instance from the runtime.
  - `_get_cog() -> Optional[UserDataCog]`: Safely retrieves the UserDataCog.
  - `get_tools() -> list`: Returns a list of LangChain tools bound to this runtime.

## Functions

No module-level functions defined in this file.

