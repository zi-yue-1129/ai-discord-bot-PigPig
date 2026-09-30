# File: `cogs/memory/embedding_providers/openai.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/memory/embedding_providers/openai.py`.

## Classes

None

## Functions

### `openai_provider(settings) -> Embeddings`
OpenAI embedding provider factory.  Expects settings to provide:   - openai_api_key   - openai_model_name  Returns a langchain_core compatible Embeddings instance.
