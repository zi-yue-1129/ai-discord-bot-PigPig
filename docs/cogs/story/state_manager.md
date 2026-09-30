# File: `cogs/story/state_manager.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/story/state_manager.py`.

## Classes

### `StoryStateManager`
Manages story state updates based on structured GM Action Plans.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `logger` (`Any`): Instance attribute logger

- **Methods**:
  - `update_state_from_gm_plan(self, instance, gm_plan) -> StoryInstance`: Updates the story state based on a structured GMActionPlan.
  - `initialize_default_state(self, instance) -> StoryInstance`: Initialize default state for a new story instance.

## Functions

None

