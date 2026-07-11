# File: `llm/tools/episodic_memory.py`

## Overview
The `EpisodicMemoryTools` class provides LangChain-compatible tools that allow an LLM Agent to query the long-term episodic memory (semantic vector store) managed by the bot's `VectorManager`. This enables the bot to "remember" past conversations, even those that occurred months ago, by performing semantic search on historical fragments.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `episodic_memory.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `EpisodicMemoryTools`
Container for episodic memory tools bound to a runtime.

This class provides LangChain-compatible tools that allow an LLM Agent
to query the long-term episodic memory (semantic vector store) managed
by the bot's VectorManager.

Usage:
    tools = EpisodicMemoryTools(runtime).get_tools()

- **Attributes**:
  - `runtime` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(runtime: Any) -> Any`: Performs internal processing logic.
  - `_get_bot() -> Optional[Any]`: Safely retrieve the bot instance from the runtime.
  - `get_tools() -> List`: Return a list of LangChain tools (closures) bound to the runtime.
