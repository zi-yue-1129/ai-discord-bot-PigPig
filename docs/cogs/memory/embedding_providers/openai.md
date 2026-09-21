# File: `cogs/memory/embedding_providers/openai.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

No classes defined.

## Functions

### `openai_provider(settings: MemoryConfig) -> Embeddings`
OpenAI embedding provider factory.

Expects settings to provide:
  - openai_api_key
  - openai_model_name

Returns a langchain_core compatible Embeddings instance.
