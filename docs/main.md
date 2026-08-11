# File: `main.py`

## Overview
`main.py` is the execution entry point for the PigPig Discord Bot. It handles environment setup, bot instantiation, and the initial connection to Discord.

## Classes

### `CommandCheck`
A custom `app_commands.CommandTree` that overrides `interaction_check` to ensure that all slash commands are executed within a server (guild) context, preventing errors in Direct Messages.

- **Methods**:
  - `interaction_check() -> bool`: Executes logic for interaction_check.

