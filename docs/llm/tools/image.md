# File: `llm/tools/image.py`

## Overview
Image generation tools for LLM integration.

This module provides LangChain-compatible tools for generating images
using the ImageGenerationCog.

## Classes

### `ImageTools`
Container class for image generation tools.

This class holds the runtime context and provides factory methods
to create tool instances bound to that context.

Attributes:
    runtime: The orchestrator request containing bot, message, and logger.

- **Attributes**:
  - `runtime` (`Any`): Instance attribute managing runtime.

- **Methods**:
  - `get_tools() -> list`: Returns a list of LangChain tools bound to this runtime.  Returns:     A list containing the generate_image tool with runtime context.

