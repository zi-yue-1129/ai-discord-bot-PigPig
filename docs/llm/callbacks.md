# File: `llm/callbacks.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `callbacks` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Classes

### `ToolFeedbackCallbackHandler`
Callback handler for providing feedback during tool execution.

- **Attributes**:
  - `message_edit` (`Any`): Instance attribute for message_edit.
  - `language_manager` (`Any`): Instance attribute for language_manager.
  - `guild_id` (`Any`): Instance attribute for guild_id.

- **Methods**:
  - `__init__(message_edit, language_manager, guild_id) -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `on_tool_start(serialized, input_str, **kwargs) -> Any`: Run when tool starts running.
