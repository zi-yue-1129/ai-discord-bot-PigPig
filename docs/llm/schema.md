# File: `llm/schema.py`

## Overview
LangChain compatible data schemas.

This file defines the Pydantic models for receiving Discord requests and returning responses.

## Classes

### `OrchestratorRequest`
Core class implementation.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `message` (`Message`): Attribute holding message data.
  - `logger` (`Any`): Attribute holding logger data.
  - `announce_new_version` (`bool`): Attribute holding announce_new_version data.

- **Methods**:
  - None specified.

### `OrchestratorResponse`
Response model returned by the orchestrator.

Attributes:
    reply: The agent's reply or structured response (type varies by provider).
    tool_calls: Optional list of tool call records represented as dicts.

- **Attributes**:
  - `reply` (`Any | None`): Attribute holding reply data.
  - `tool_calls` (`List[Dict] | None`): Attribute holding tool_calls data.

- **Methods**:
  - None specified.

## Functions

No top-level functions defined.
