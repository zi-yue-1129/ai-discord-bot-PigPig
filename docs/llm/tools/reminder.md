# File: `llm/tools/reminder.py`

## Overview
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
  - `runtime` (`Any`): Attribute holding runtime data.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> Any`: Initializes ReminderTools with runtime context.
  - `get_tools() -> list`: Returns a list of LangChain tools bound to this runtime.

## Functions

No top-level functions defined.
