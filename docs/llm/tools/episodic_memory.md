# File: `llm/tools/episodic_memory.py`

## Overview
Core file handling responsibilities within the `llm/tools` subsystem.

## Classes

### `EpisodicMemoryTools`
Container for episodic memory tools bound to a runtime.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(runtime: Any) -> Any`: No description provided.
  - `_get_bot() -> Optional[Any]`: Safely retrieve the bot instance from the runtime.
  - `get_tools() -> List`: Return a list of LangChain tools (closures) bound to the runtime.

## Functions

No module-level functions defined in this file.

