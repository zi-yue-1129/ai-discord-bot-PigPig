# File: `llm/callbacks.py`

## Overview
This file is part of the llm subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `ToolFeedbackCallbackHandler`
Callback handler for providing feedback during tool execution.

- **Attributes**:
  - `message_edit` (`Any`): Attribute holding message_edit data.
  - `language_manager` (`Any`): Attribute holding language_manager data.
  - `guild_id` (`Any`): Attribute holding guild_id data.

- **Methods**:
  - `__init__(message_edit: Any, language_manager: Any, guild_id: str) -> Any`: Executes __init__ logic.
  - `on_tool_start(serialized: Dict[Tuple[str, Any]], input_str: str, **kwargs, run_id: UUID, parent_run_id: Optional[UUID], tags: Optional[List[str]], metadata: Optional[Dict[Tuple[str, Any]]]) -> Any`: Run when tool starts running.

## Functions

No top-level functions defined.
