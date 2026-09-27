# File: `llm/tools/episodic_memory.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `episodic_memory` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `EpisodicMemoryTools`
Container for episodic memory tools bound to a runtime.

This class provides LangChain-compatible tools that allow an LLM Agent
to query the long-term episodic memory (semantic vector store) managed
by the bot's VectorManager.

Usage:
    tools = EpisodicMemoryTools(runtime).get_tools()

- **Attributes**:
  - `runtime` (`Any`): Instance attribute for runtime.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(runtime) -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `_get_bot() -> Optional[...]`: Safely retrieve the bot instance from the runtime.
  - `get_tools() -> List`: Return a list of LangChain tools (closures) bound to the runtime.
