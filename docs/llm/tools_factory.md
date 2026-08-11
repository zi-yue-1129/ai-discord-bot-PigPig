# File: `llm/tools_factory.py`

## Overview
Factory for LangChain tools that auto-loads only @tool-decorated functions.

Design Points:
- Automatically loads modules under the `llm/tools/` folder (if it exists).
- Only collects callables or BaseTool instances decorated with LangChain's `@tool`.
- Implements permission-based filtering (admin/moderator) and agent mode routing.
- Exceptions are reported asynchronously via `func.report_error`, with logger fallback.
- Uses a caching mechanism to avoid repeated disk scans, improving performance.

## Functions

### `get_tools(user, guid, runtime, agent_mode) -> List[BaseTool]`
Returns a list of LangChain tools available to the Discord user based on permissions.

Permission Strategy:
- Tools can declare a `required_permission` attribute (string, e.g., "admin", "moderator").
- If declared, only users with that permission will receive the tool.
- If undeclared, the tool is open to all users.

Routing Strategy (target_agent_mode):
- Tools can specify which Agent they belong to via `target_agent_mode`.
- Supported values:
    - "info" (Default) - Only for the Info Agent.
    - "message" - Only for the Message Agent.
    - "all" - Available to both Agents.
- Discovery order for the attribute:
    1. metadata["target_agent_mode"]
    2. direct attribute on tool instance
    3. attribute on original callable

Args:
    user: The Discord user.
    guid: The Discord Guild.
    runtime: Execution runtime context.
    agent_mode: Filtering mode ("all", "info", "message").
        - "all": Return all available tools.
        - "info": Return tools for Info Agent (excludes message-only tools).
        - "message": Return tools for Message Agent (excludes info-only tools).

Returns:
    List[BaseTool]: List of filtered tools compatible with LangChain.

