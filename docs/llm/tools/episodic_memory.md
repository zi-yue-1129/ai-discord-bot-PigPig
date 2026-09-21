# File: `llm/tools/episodic_memory.py`

## Overview
This file is part of the llm subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `EpisodicMemoryTools`
Container for episodic memory tools bound to a runtime.

This class provides LangChain-compatible tools that allow an LLM Agent
to query the long-term episodic memory (semantic vector store) managed
by the bot's VectorManager.

Usage:
    tools = EpisodicMemoryTools(runtime).get_tools()

- **Attributes**:
  - `runtime` (`Any`): Attribute holding runtime data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(runtime: Any) -> Any`: Executes __init__ logic.
  - `_get_bot() -> Optional[Any]`: Safely retrieve the bot instance from the runtime.
  - `get_tools() -> List`: Return a list of LangChain tools (closures) bound to the runtime.

## Functions

No top-level functions defined.
