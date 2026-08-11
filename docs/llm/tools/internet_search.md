# File: `llm/tools/internet_search.py`

## Overview
Internet search tools for LLM integration.

This module provides LangChain-compatible tools for performing various types
of internet searches using the InternetSearchCog.

## Classes

### `InternetSearchTools`
Container class for internet search tools.

This class holds the runtime context and provides factory methods
to create tool instances bound to that context.

Attributes:
    runtime: The orchestrator request containing bot, message, and logger.

- **Attributes**:
  - `runtime` (`Any`): Instance attribute managing runtime.

- **Methods**:
  - `get_tools() -> list`: Returns a list of LangChain tools bound to this runtime.  Returns:     A list containing the internet_search tool with runtime context.

