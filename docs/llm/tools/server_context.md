# File: `llm/tools/server_context.py`

## Overview
The `ServerContextTools` class provides a suite of tools that allow the AI agent to inspect its surroundings within Discord. These tools provide real-time information about the current server (guild), specific channels, and individual user profiles, including their current activities and roles.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `server_context.py`, providing vital integrations within the PigPig bot ecosystem.
Server context tools for LLM integration.

Provides tools for the AI agent to query Discord server, channel, and
member information at runtime. All tools are routed to the info_agent
via target_agent_mode = "info".

## Classes

### `ServerContextTools`
Container for Discord server/channel/user info query tools.

- **Attributes**:
  - `runtime` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> None`: Performs internal processing logic.
  - `get_tools() -> list`: Return server context query tools.
