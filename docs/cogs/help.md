# File: `cogs/help.py`

## Overview
The Help cog provides a comprehensive command help system with multi-language support. It dynamically generates help content by inspecting all loaded cogs and their available commands.

## Classes

### `HelpCog`
Manages the state and core operations for HelpCog.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.

- **Methods**:
  - `cog_load() -> Any`: 當 Cog 載入時初始化語言管理器
  - `help_command(interaction) -> Any`: Executes logic for help_command.

## Functions

### `setup(bot) -> Any`
Performs setup operations.

