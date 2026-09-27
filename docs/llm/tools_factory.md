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

### `_report_async(exc, ctx) -> None`
Report an error asynchronously; falls back to logger on failure.

### `_compute_pkg_dir_mtime(pkg_dir) -> float`
Calculate the maximum mtime of all .py files in the package directory.

### `_discover_tools_package() -> Iterable[...]`
Import and return all modules under llm/tools (if the directory exists).

### `_is_decorated_tool(obj) -> bool`
Check if an object is a LangChain tool (BaseTool or @tool-decorated callable).

### `_extract_tools_from_module(mod, runtime) -> List[...]`
Collect tools from a module using get_tools() discovery.

### `_get_user_permissions(user, guid) -> dict`
Retrieve Discord user permission info from the project's PermissionValidator.

### `get_tools(user, guid, runtime, agent_mode) -> List[...]`
Returns a list of LangChain tools available to the Discord user based on permissions.
