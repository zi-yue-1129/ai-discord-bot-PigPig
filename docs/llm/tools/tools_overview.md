# File: `llm/tools/tools_overview.py`

## Overview
The `ToolsOverviewTools` class provides a dynamic LangChain-compatible tool that discovers and summarizes all available tools in the llm.tools package. It uses automatic introspection to generate comprehensive tool listings without hard-coded dependencies.

## Classes

### `ToolsOverviewTools`
Container for a tool that lists available tools and their short descriptions.

Usage:
    tools = ToolsOverviewTools(runtime).get_tools()

- **Attributes**:
  - `runtime` (`Any`): Instance attribute managing runtime.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `get_tools() -> List`: Return a list containing a single tool that summarizes available tools.  The returned tool inspects modules under the llm.tools package, instantiates any discovered '*Tools' container classes (passing the current runtime), calls their get_tools() methods, and extracts each tool function's name, signature, and first-line docstring as a short description.  This process is automatic and does not rely on hard-coded tool lists.

