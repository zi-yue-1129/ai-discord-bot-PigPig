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
  - `runtime` (`Any`): Instance attribute managing runtime.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `get_tools() -> list`: Return server context query tools.

