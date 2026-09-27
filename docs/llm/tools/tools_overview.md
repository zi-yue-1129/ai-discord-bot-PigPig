# File: `llm/tools/tools_overview.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `tools_overview` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `ToolsOverviewTools`
Container for a tool that lists available tools and their short descriptions.

Usage:
    tools = ToolsOverviewTools(runtime).get_tools()

- **Attributes**:
  - `runtime` (`Any`): Instance attribute for runtime.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(runtime) -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `get_tools() -> List`: Return a list containing a single tool that summarizes available tools.
