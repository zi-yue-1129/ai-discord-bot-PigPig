# File: `llm/tools/reminder.py`

## Overview
The `ReminderTools` class provides LangChain-compatible tools for setting and managing reminders using the ReminderCog. It enables agents to schedule future notifications for users with flexible time specifications.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `reminder.py`, providing vital integrations within the PigPig bot ecosystem.
Reminder tools for LLM integration.

This module provides LangChain-compatible tools for setting reminders
using the ReminderCog.

## Classes

### `ReminderTools`
Container class for reminder management tools.

This class holds the runtime context and provides factory methods
to create tool instances bound to that context.

Attributes:
    runtime: The orchestrator request containing bot, message, and logger.

- **Attributes**:
  - `runtime` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> Any`: Initializes ReminderTools with runtime context.
  - `get_tools() -> list`: Returns a list of LangChain tools bound to this runtime.
