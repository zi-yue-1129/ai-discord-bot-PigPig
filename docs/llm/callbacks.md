# File: `llm/callbacks.py`

## Overview
The `llm.callbacks` module implements custom LangChain callback handlers to provide real-time feedback to Discord users during complex AI reasoning and tool execution processes.

## Classes

### `ToolFeedbackCallbackHandler`
Callback handler for providing feedback during tool execution.

- **Attributes**:
  - `message_edit` (`Any`): Instance attribute managing message_edit.
  - `language_manager` (`Any`): Instance attribute managing language_manager.
  - `guild_id` (`Any`): Instance attribute managing guild_id.

- **Methods**:
  - `on_tool_start(serialized, input_str, **kwargs) -> Any`: Run when tool starts running.

