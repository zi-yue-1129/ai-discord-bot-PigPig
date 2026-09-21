# File: `llm/tools/tools_overview.py`

## Overview
This file is part of the llm subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `ToolsOverviewTools`
Container for a tool that lists available tools and their short descriptions.

Usage:
    tools = ToolsOverviewTools(runtime).get_tools()

- **Attributes**:
  - `runtime` (`Any`): Attribute holding runtime data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(runtime: Any) -> Any`: Executes __init__ logic.
  - `get_tools() -> List`: Return a list containing a single tool that summarizes available tools.

## Functions

No top-level functions defined.
