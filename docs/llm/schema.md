# File: `llm/schema.py`

## Overview
LangChain compatible data schemas.

This file defines the Pydantic models for receiving Discord requests and returning responses.

## Classes

### `OrchestratorRequest`
Represents the `OrchestratorRequest` class in the system.

- **Attributes**:
  - `bot` (`Any`): Class attribute representing bot.
  - `message` (`Message`): Class attribute representing message.
  - `logger` (`Any`): Class attribute representing logger.
  - `announce_new_version` (`bool`): Class attribute representing announce_new_version.

### `OrchestratorResponse`
Response model returned by the orchestrator.

Attributes:
    reply: The agent's reply or structured response (type varies by provider).
    tool_calls: Optional list of tool call records represented as dicts.

- **Attributes**:
  - `reply` (`Any`): Class attribute representing reply.
  - `tool_calls` (`Any`): Class attribute representing tool_calls.
