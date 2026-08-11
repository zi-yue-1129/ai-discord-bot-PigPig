# File: `cogs/story/state_manager.py`

## Overview
Core responsibilities and logic for `cogs/story/state_manager.py`. This module is part of the cogs subsystem and handles the associated business logic, state management, and integrations.

## Classes

### `StoryStateManager`
Manages story state updates based on structured GM Action Plans.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `logger` (`Any`): Instance attribute managing logger.

- **Methods**:
  - `update_state_from_gm_plan(instance, gm_plan) -> StoryInstance`: Updates the story state based on a structured GMActionPlan.
  - `initialize_default_state(instance) -> StoryInstance`: Initialize default state for a new story instance.

