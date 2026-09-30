# File: `cogs/memory/embedding_providers/google.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/memory/embedding_providers/google.py`.

## Classes

None

## Functions

### `google_genai_provider(settings) -> Embeddings`
Google Generative AI embeddings provider using langchain_google_genai.  Expects settings to provide:   - google_api_key   - embedding_model_name  Returns a langchain_core compatible Embeddings instance.
