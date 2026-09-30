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
  - `runtime` (`Any`): Instance attribute runtime
  - `logger` (`Any`): Instance attribute logger
  - `_checker` (`Any`): Instance attribute _checker

- **Methods**:
  - `get_tools(self) -> list`: Return bot info tools.

## Functions

### `_get_checker() -> 'VersionChecker'`
Function _get_checker.

