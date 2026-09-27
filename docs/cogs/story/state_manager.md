# File: `cogs/story/state_manager.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `state_manager` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `StoryStateManager`
Manages story state updates based on structured GM Action Plans.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `logger` (`Any`): Instance attribute for logger.

- **Methods**:
  - `__init__(bot) -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `update_state_from_gm_plan(instance, gm_plan) -> StoryInstance`: Updates the story state based on a structured GMActionPlan.
  - `initialize_default_state(instance) -> StoryInstance`: Initialize default state for a new story instance.
