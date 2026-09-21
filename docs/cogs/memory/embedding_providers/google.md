# File: `cogs/memory/embedding_providers/google.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

No classes defined.

## Functions

### `google_genai_provider(settings: MemoryConfig) -> Embeddings`
Google Generative AI embeddings provider using langchain_google_genai.

Expects settings to provide:
  - google_api_key
  - embedding_model_name

Returns a langchain_core compatible Embeddings instance.
