# File: `llm/tools/bot_info.py`

## Overview
The `BotInfoTools` class provides tools for the AI agent to query information about the bot itself, specifically its version history and recent updates from GitHub. This allows the bot to answer questions like "What's new?" or "What version are you running?".

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `bot_info.py`, providing vital integrations within the PigPig bot ecosystem.
Bot info tools for LLM integration.

Provides a tool for the AI agent to query the bot's own GitHub release
history to answer questions about recent updates and changelog.
All tools are routed to the info_agent via target_agent_mode = "info".

## Classes

### `BotInfoTools`
Container for bot self-information tools.

- **Attributes**:
  - `runtime` (`Any`): Internal instance state.
  - `logger` (`Any`): Internal instance state.
  - `_checker` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> None`: Performs internal processing logic.
  - `get_tools() -> list`: Return bot info tools.

## Functions

### `_get_checker() -> VersionChecker`
Performs internal processing logic.
