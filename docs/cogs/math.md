# File: `cogs/math.py`

## Overview
The Math cog provides comprehensive mathematical calculation capabilities through Discord slash commands. It supports basic arithmetic, advanced mathematical operations, unit conversions, and statistical calculations with multi-language support.

## Classes

### `MathCalculatorCog`
Cog for advanced mathematical calculations using SymPy.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.

- **Methods**:
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `calculate_math(expression, message_to_edit, guild_id) -> str`: Parse and evaluate a mathematical expression, returning a localized result string.

## Functions

### `setup(bot) -> Any`
Set up the MathCalculatorCog.

