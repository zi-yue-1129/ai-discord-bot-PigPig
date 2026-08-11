# File: `llm/tools/episodic_memory.py`

## Overview
The `EpisodicMemoryTools` class provides LangChain-compatible tools that allow an LLM Agent to query the long-term episodic memory (semantic vector store) managed by the bot's `VectorManager`. This enables the bot to "remember" past conversations, even those that occurred months ago, by performing semantic search on historical fragments.

## Classes

### `EpisodicMemoryTools`
Container for episodic memory tools bound to a runtime.

This class provides LangChain-compatible tools that allow an LLM Agent
to query the long-term episodic memory (semantic vector store) managed
by the bot's VectorManager.

Usage:
    tools = EpisodicMemoryTools(runtime).get_tools()

- **Attributes**:
  - `runtime` (`Any`): Instance attribute managing runtime.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `get_tools() -> List`: Return a list of LangChain tools (closures) bound to the runtime.

