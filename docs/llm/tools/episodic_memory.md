# File: `llm/tools/episodic_memory.py`

## Overview
This file is part of the LLM integration and orchestration pipeline and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `llm/tools/episodic_memory.py`.

## Classes

### `EpisodicMemoryTools`
Container for episodic memory tools bound to a runtime.  This class provides LangChain-compatible tools that allow an LLM Agent to query the long-term episodic memory (semantic vector store) managed by the bot's VectorManager.  Usage:     tools = EpisodicMemoryTools(runtime).get_tools()

- **Attributes**:
  - `runtime` (`Any`): Instance attribute runtime
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `_get_bot(self) -> Optional[Any]`: Safely retrieve the bot instance from the runtime.
  - `get_tools(self) -> List`: Return a list of LangChain tools (closures) bound to the runtime.

## Functions

None

