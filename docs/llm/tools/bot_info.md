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
  - `runtime` (`Any`): Instance attribute for runtime.
  - `logger` (`Any`): Instance attribute for logger.
  - `_checker` (`Any`): Instance attribute for _checker.

- **Methods**:
  - `__init__(runtime) -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `_get_checker`.
  - `get_tools() -> list`: Return bot info tools.

## Functions

### `_get_checker() -> VersionChecker`
Provides `_get_checker` functionality. Internally, it interacts with methods like `VersionChecker`.
