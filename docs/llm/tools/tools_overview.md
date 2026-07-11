# File: `llm/tools/tools_overview.py`

## Overview
The `ToolsOverviewTools` class provides a dynamic LangChain-compatible tool that discovers and summarizes all available tools in the llm.tools package. It uses automatic introspection to generate comprehensive tool listings without hard-coded dependencies.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `tools_overview.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `ToolsOverviewTools`
Container for a tool that lists available tools and their short descriptions.

Usage:
    tools = ToolsOverviewTools(runtime).get_tools()

- **Attributes**:
  - `runtime` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(runtime: Any) -> Any`: Performs internal processing logic.
  - `get_tools() -> List`: Return a list containing a single tool that summarizes available tools.
