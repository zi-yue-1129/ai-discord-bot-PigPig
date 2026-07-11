# File: `llm/callbacks.py`

## Overview
The `llm.callbacks` module implements custom LangChain callback handlers to provide real-time feedback to Discord users during complex AI reasoning and tool execution processes.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `callbacks.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `ToolFeedbackCallbackHandler`
Callback handler for providing feedback during tool execution.

- **Attributes**:
  - `message_edit` (`Any`): Internal instance state.
  - `language_manager` (`Any`): Internal instance state.
  - `guild_id` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(message_edit: Any, language_manager: Any, guild_id: str) -> Any`: Performs internal processing logic.
  - `on_tool_start(serialized: Dict[Tuple], input_str: str) -> Any`: Run when tool starts running.
