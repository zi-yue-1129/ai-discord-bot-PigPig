# File: `llm/tools_factory.py`

## Overview
Factory for LangChain tools that auto-loads only @tool-decorated functions.

## Classes

No classes defined in this file.

## Functions

### `_report_async(exc: Exception, ctx: str) -> None`
Report an error asynchronously; falls back to logger on failure.

### `_compute_pkg_dir_mtime(pkg_dir: str) -> float`
Calculate the maximum mtime of all .py files in the package directory.

### `_discover_tools_package() -> Iterable[Any]`
Import and return all modules under llm/tools (if the directory exists).

### `_is_decorated_tool(obj: Any) -> bool`
Check if an object is a LangChain tool (BaseTool or @tool-decorated callable).

### `_extract_tools_from_module(mod: Any, runtime: str) -> List[Any]`
Collect tools from a module using get_tools() discovery.

### `_get_user_permissions(user: discord.Member, guid: discord.Guild) -> dict`
Retrieve Discord user permission info from the project's PermissionValidator.

### `get_tools(user: discord.Member, guid: discord.Guild, runtime: OrchestratorRequest, agent_mode: str) -> List[BaseTool]`
Returns a list of LangChain tools available to the Discord user based on permissions.

