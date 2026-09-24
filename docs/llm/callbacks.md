# File: `llm/callbacks.py`

## Overview
Core file handling responsibilities within the `llm` subsystem.

## Classes

### `ToolFeedbackCallbackHandler`
Callback handler for providing feedback during tool execution.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(message_edit: Any, language_manager: Any, guild_id: str) -> Any`: No description provided.
  - `on_tool_start(serialized: Dict[Tuple[str, Any]], input_str: str, run_id: UUID, parent_run_id: Optional[UUID], tags: Optional[List[str]], metadata: Optional[Dict[Tuple[str, Any]]], **kwargs: Any) -> Any`: Run when tool starts running.

## Functions

No module-level functions defined in this file.

