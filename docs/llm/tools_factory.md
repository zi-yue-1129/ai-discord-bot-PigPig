# File: `llm/tools_factory.py`

## Overview
Factory for LangChain tools that auto-loads only @tool-decorated functions.

Design Points:
- Automatically loads modules under the `llm/tools/` folder (if it exists).
- Only collects callables or BaseTool instances decorated with LangChain's `@tool`.
- Implements permission-based filtering (admin/moderator) and agent mode routing.
- Exceptions are reported asynchronously via `func.report_error`, with logger fallback.
- Uses a caching mechanism to avoid repeated disk scans, improving performance.

## Classes

No classes defined.

## Functions

### `_report_async(exc: Exception, ctx: str) -> None`
Report an error asynchronously; falls back to logger on failure.

### `_compute_pkg_dir_mtime(pkg_dir: str) -> float`
Calculate the maximum mtime of all .py files in the package directory.

### `_discover_tools_package() -> Iterable[Any]`
Import and return all modules under llm/tools (if the directory exists).

### `_is_decorated_tool(obj: Any) -> bool`
Check if an object is a LangChain tool (BaseTool or @tool-decorated callable).

### `_extract_tools_from_module(mod: Any, runtime: OrchestratorRequest) -> List[Any]`
Collect tools from a module using get_tools() discovery.

Strategies:
- If the module provides a module-level `get_tools(runtime)`, use its returned list.
- Otherwise, find classes ending in `Tools`, instantiate them with `runtime`,
  and call `instance.get_tools()`.
- Does not scan individual members or arbitrary classes.
- Reports errors if `get_tools()` returns a coroutine instead of a list.

### `_get_user_permissions(user: discord.Member, guid: discord.Guild) -> dict`
Retrieve Discord user permission info from the project's PermissionValidator.

Tries to import `cogs.system_prompt.permissions` and validate the user.
Falls back to a conservative default (non-admin, non-moderator) if it fails.

### `get_tools(user: discord.Member, guid: discord.Guild, runtime: OrchestratorRequest, agent_mode: str) -> List[BaseTool]`
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
