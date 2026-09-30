# File: `llm/callbacks.py`

## Overview
This file is part of the LLM integration and orchestration pipeline and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `llm/callbacks.py`.

## Classes

### `ToolFeedbackCallbackHandler`
Callback handler for providing feedback during tool execution.

- **Attributes**:
  - `message_edit` (`Any`): Instance attribute message_edit
  - `language_manager` (`Any`): Instance attribute language_manager
  - `guild_id` (`Any`): Instance attribute guild_id

- **Methods**:
  - `on_tool_start(self, serialized, input_str, **kwargs) -> Any`: Run when tool starts running.

## Functions

None

