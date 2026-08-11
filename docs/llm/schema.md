# File: `llm/schema.py`

## Overview
LangChain compatible data schemas.

This file defines the Pydantic models for receiving Discord requests and returning responses.

## Classes

### `OrchestratorRequest`
```python
@dataclass
class OrchestratorRequest:
    bot: Any
    message: Message
    logger: Any
```

**Purpose:** Contains runtime context for orchestrator operations

**Fields:**
- `bot`: Discord bot instance
- `message`: Discord message object being processed
- `logger`: Logger instance for this request

**Usage:**
```python
runtime_context = OrchestratorRequest(
    bot=discord_bot,
    message=discord_message,
    logger=logging_logger
)
```

- **Attributes**:
  - `bot` (`Any`): Stores data related to bot.
  - `message` (`Message`): Stores data related to message.
  - `logger` (`Any`): Stores data related to logger.
  - `announce_new_version` (`bool`): Stores data related to announce_new_version.

### `OrchestratorResponse`
Response model returned by the orchestrator.

Attributes:
    reply: The agent's reply or structured response (type varies by provider).
    tool_calls: Optional list of tool call records represented as dicts.

- **Attributes**:
  - `reply` (`Any | None`): Stores data related to reply.
  - `tool_calls` (`List[Dict] | None`): Stores data related to tool_calls.

