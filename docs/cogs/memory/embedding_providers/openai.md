# File: `cogs/memory/embedding_providers/openai.py`

## Overview
Core logic and functionalities for openai.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Functions

### `openai_provider(settings) -> Embeddings`
OpenAI embedding provider factory.

Expects settings to provide:
  - openai_api_key
  - openai_model_name

Returns a langchain_core compatible Embeddings instance.
