# File: `llm/tools/server_context.py`

## Overview
Server context tools for LLM integration.

Provides tools for the AI agent to query Discord server, channel, and
member information at runtime. All tools are routed to the info_agent
via target_agent_mode = "info".

## Classes

### `ServerContextTools`
Container for Discord server/channel/user info query tools.

- **Attributes**:
  - `runtime` (`Any`): Instance attribute for runtime.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(runtime) -> None`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `get_tools() -> list`: Return server context query tools.
