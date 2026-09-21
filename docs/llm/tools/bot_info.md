# File: `llm/tools/bot_info.py`

## Overview
Bot info tools for LLM integration.

Provides a tool for the AI agent to query the bot's own GitHub release
history to answer questions about recent updates and changelog.
All tools are routed to the info_agent via target_agent_mode = "info".

## Classes

### `BotInfoTools`
Container for bot self-information tools.

- **Attributes**:
  - `runtime` (`Any`): Attribute holding runtime data.
  - `logger` (`Any`): Attribute holding logger data.
  - `_checker` (`Any`): Attribute holding _checker data.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> None`: Executes __init__ logic.
  - `get_tools() -> list`: Return bot info tools.

## Functions

### `_get_checker() -> VersionChecker`
Performs _get_checker operations.
