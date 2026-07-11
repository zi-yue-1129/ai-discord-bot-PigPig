# File: `llm/tools/image.py`

## Overview
The `ImageTools` class provides LangChain-compatible tools for generating images using the `ImageGenerationCog`. It allows the LLM to create visual content based on text descriptions, supporting both text-to-image and image-to-image (img2img) workflows.

This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `image.py`, providing vital integrations within the PigPig bot ecosystem.
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
  - `runtime` (`Any`): Internal instance state.

- **Methods**:
  - `__init__(runtime: OrchestratorRequest) -> Any`: Initializes ImageTools with runtime context.
  - `get_tools() -> list`: Returns a list of LangChain tools bound to this runtime.
