### Create File: docs/cogs/memory/embedding_providers/vllm_provider.md
# File: `cogs/memory/embedding_providers/vllm_provider.py`

## Overview
Core module for cogs/memory/embedding_providers/vllm_provider.py. Handles relevant business logic and components.

## Classes

No classes defined in this file.

## Functions

### `vllm_provider(settings) -> Embeddings`
vLLM embedding provider factory.  vLLM exposes an OpenAI-compatible /v1/embeddings endpoint, so this routes through OpenAIEmbeddings with a custom base_url and the api_key vLLM was launched with (VLLM_API_KEY in .env; falls back to the "EMPTY" placeholder vLLM accepts when --api-key is not set).  Expects settings to provide:   - embedding_model_name (the --served-model-name vLLM was launched with)   - vllm_url (e.g. http://127.0.0.1:8182)
