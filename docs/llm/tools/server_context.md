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
  - `runtime` (`Any`): Attribute holding runtime data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> None`: Executes __init__ logic.
  - `get_tools() -> list`: Return server context query tools.

## Functions

No top-level functions defined.
