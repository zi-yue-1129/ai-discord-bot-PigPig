# File: `cogs/memory/embedding_providers/vllm_provider.py`

## Overview
Core responsibilities and logic for `cogs/memory/embedding_providers/vllm_provider.py`. This module is part of the cogs subsystem and handles the associated business logic, state management, and integrations.

## Functions

### `vllm_provider(settings) -> Embeddings`
vLLM embedding provider factory.

vLLM exposes an OpenAI-compatible /v1/embeddings endpoint, so this routes
through OpenAIEmbeddings with a custom base_url and a placeholder api_key.

Expects settings to provide:
  - embedding_model_name (the --served-model-name vLLM was launched with)
  - vllm_url (e.g. http://127.0.0.1:8182)
