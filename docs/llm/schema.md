# File: `llm/schema.py`

## Overview
LangChain compatible data schemas.

This file defines the Pydantic models for receiving Discord requests and returning responses.

## Classes

### `OrchestratorRequest`
Class representing OrchestratorRequest.

- **Attributes**:
  - `bot` (`Any`): Attribute bot
  - `message` (`Message`): Attribute message
  - `logger` (`Any`): Attribute logger
  - `announce_new_version` (`bool`): Attribute announce_new_version

- **Methods**:
  - None

### `OrchestratorResponse`
Response model returned by the orchestrator.  Attributes:     reply: The agent's reply or structured response (type varies by provider).     tool_calls: Optional list of tool call records represented as dicts.

- **Attributes**:
  - `reply` (`Any | None`): Attribute reply
  - `tool_calls` (`List[Dict] | None`): Attribute tool_calls

- **Methods**:
  - None

## Functions

None

