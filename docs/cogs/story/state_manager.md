# File: `cogs/story/state_manager.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `StoryStateManager`
Manages story state updates based on structured GM Action Plans.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `logger` (`Any`): Attribute holding logger data.

- **Methods**:
  - `__init__(bot) -> Any`: Executes __init__ logic.
  - `update_state_from_gm_plan(instance: StoryInstance, gm_plan: GMActionPlan) -> StoryInstance`: Updates the story state based on a structured GMActionPlan.
  - `initialize_default_state(instance: StoryInstance) -> StoryInstance`: Initialize default state for a new story instance.

## Functions

No top-level functions defined.
