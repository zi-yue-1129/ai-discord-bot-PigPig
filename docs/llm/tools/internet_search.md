# File: `llm/tools/internet_search.py`

## Overview
The `InternetSearchTools` class provides LangChain-compatible tools for performing various types of internet searches using the InternetSearchCog. It supports multiple search types and integrates with Gemini grounding when available.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `internet_search.py`, providing vital integrations within the PigPig bot ecosystem.
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
  - `runtime` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> Any`: Initializes InternetSearchTools with runtime context.
  - `get_tools() -> list`: Returns a list of LangChain tools bound to this runtime.
