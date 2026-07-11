# File: `llm/schema.py`

## Overview
The `schema.py` module defines LangChain-compatible data structures for Discord bot requests and responses. These Pydantic models ensure type safety and validation across the LLM integration layer.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `schema.py`, providing vital integrations within the PigPig bot ecosystem.
LangChain compatible data schemas.

This file defines the Pydantic models for receiving Discord requests and returning responses.

## Classes

### `OrchestratorRequest`
Class managing OrchestratorRequest state and behavior.

- **Attributes**:
  - `bot` (`Any`): Property holding the bot state.
  - `message` (`Message`): Property holding the message state.
  - `logger` (`Any`): Property holding the logger state.
  - `announce_new_version` (`bool`): Property holding the announce_new_version state.

### `OrchestratorResponse`
Response model returned by the orchestrator.

Attributes:
    reply: The agent's reply or structured response (type varies by provider).
    tool_calls: Optional list of tool call records represented as dicts.

- **Attributes**:
  - `reply` (`Any`): Property holding the reply state.
  - `tool_calls` (`Any`): Property holding the tool_calls state.
