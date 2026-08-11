# File: `cogs/memory/embedding_providers/google.py`

## Overview
Core logic and functionalities for google.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Functions

### `google_genai_provider(settings) -> Embeddings`
Google Generative AI embeddings provider using langchain_google_genai.

Expects settings to provide:
  - google_api_key
  - embedding_model_name

Returns a langchain_core compatible Embeddings instance.
