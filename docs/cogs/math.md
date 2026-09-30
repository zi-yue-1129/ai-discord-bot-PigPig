# File: `cogs/math.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/math.py`.

## Classes

### `MathCalculatorCog`
Cog for advanced mathematical calculations using SymPy.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `lang_manager` (`Optional[LanguageManager]`): Instance attribute lang_manager

- **Methods**:
  - `cog_load(self) -> Any`: Initialize LanguageManager when the cog is loaded.
  - `calculate_math(self, expression, message_to_edit, guild_id) -> str`: Parse and evaluate a mathematical expression, returning a localized result string.

## Functions

### `setup(bot) -> Any`
Set up the MathCalculatorCog.

