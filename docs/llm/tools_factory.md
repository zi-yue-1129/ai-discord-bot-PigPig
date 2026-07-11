# File: `llm/tools_factory.py`

## Overview
The `tools_factory.py` module provides a factory system for dynamically loading and filtering LangChain tools based on user permissions. It automatically discovers tools from the `llm/tools/` package and provides permission-based access control for Discord users.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `tools_factory.py`, providing vital integrations within the PigPig bot ecosystem.
Factory for LangChain tools that auto-loads only @tool-decorated functions.

Design Points:
- Automatically loads modules under the `llm/tools/` folder (if it exists).
- Only collects callables or BaseTool instances decorated with LangChain's `@tool`.
- Implements permission-based filtering (admin/moderator) and agent mode routing.
- Exceptions are reported asynchronously via `func.report_error`, with logger fallback.
- Uses a caching mechanism to avoid repeated disk scans, improving performance.

## Classes

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

### `_get_user_permissions(user: discord.Member, guid: discord.Guild) -> dict`
Retrieve Discord user permission info from the project's PermissionValidator.

### `get_tools(user: discord.Member, guid: discord.Guild, runtime: OrchestratorRequest, agent_mode: str) -> List[BaseTool]`
Returns a list of LangChain tools available to the Discord user based on permissions.
