# File: `cogs/memory/embedding_providers/ollama.py`

## Overview
Core logic and functionalities for ollama.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Functions

### `ollama_provider(settings) -> Embeddings`
Ollama embedding provider factory using langchain_ollama.OllamaEmbeddings.

Expects settings to provide:
  - embedding_model_name
  - ollama_url (optional, if the client needs a custom endpoint)

Returns a langchain_core compatible Embeddings instance.
