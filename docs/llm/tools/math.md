# File: `llm/tools/math.py`

## Overview
The `MathTools` class provides LangChain-compatible tools for performing mathematical calculations using the MathCalculatorCog. It enables agents to perform complex mathematical operations through natural language expressions.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `math.py`, providing vital integrations within the PigPig bot ecosystem.
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
  - `runtime` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> Any`: Initializes MathTools with runtime context.
  - `get_tools() -> list`: Returns a list of LangChain tools bound to this runtime.
