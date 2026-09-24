# File: `llm/schema.py`

## Overview
LangChain compatible data schemas.

## Classes

### `OrchestratorRequest`
No description provided.

- **Attributes**:
  - `bot` (`Any`): Class attribute
  - `message` (`Message`): Class attribute
  - `logger` (`Any`): Class attribute
  - `announce_new_version` (`bool`): Class attribute

- **Methods**:
  - None specified.

### `OrchestratorResponse`
Response model returned by the orchestrator.

- **Attributes**:
  - `reply` (`Any | None`): Class attribute
  - `tool_calls` (`List[Dict] | None`): Class attribute

- **Methods**:
  - None specified.

## Functions

No module-level functions defined in this file.

