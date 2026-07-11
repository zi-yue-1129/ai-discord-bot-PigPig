# File: `cogs/math.py`

## Overview
The Math cog provides comprehensive mathematical calculation capabilities through Discord slash commands. It supports basic arithmetic, advanced mathematical operations, unit conversions, and statistical calculations with multi-language support.

This file belongs to the Discord Cogs Subsystem. Its core responsibility is to handle logic related to `math.py`, providing vital integrations within the PigPig bot ecosystem.

## Classes

### `MathCalculatorCog`
Cog for advanced mathematical calculations using SymPy.

- **Attributes**:
  - `bot` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(bot: Any) -> Any`: Performs internal processing logic.
  - `cog_load() -> Any`: Initialize LanguageManager when the cog is loaded.
  - `calculate_math(expression: str, message_to_edit: Any, guild_id: Optional[str]) -> str`: Parse and evaluate a mathematical expression, returning a localized result string.

## Functions

### `setup(bot: Any) -> Any`
Set up the MathCalculatorCog.
