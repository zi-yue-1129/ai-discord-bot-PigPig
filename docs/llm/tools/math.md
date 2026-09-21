# File: `llm/tools/math.py`

## Overview
Math calculation tools for LLM integration.

This module provides LangChain-compatible tools for performing mathematical
calculations using the MathCalculatorCog.

## Classes

### `MathTools`
Container class for mathematical calculation tools.

This class holds the runtime context and provides factory methods
to create tool instances bound to that context.

Attributes:
    runtime: The orchestrator request containing bot, message, and logger.

- **Attributes**:
  - `runtime` (`Any`): Attribute holding runtime data.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> Any`: Initializes MathTools with runtime context.
  - `get_tools() -> list`: Returns a list of LangChain tools bound to this runtime.

## Functions

No top-level functions defined.
