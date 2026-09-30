# File: `cogs/memory/embedding_providers/ollama.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/memory/embedding_providers/ollama.py`.

## Classes

None

## Functions

### `ollama_provider(settings) -> Embeddings`
Ollama embedding provider factory using langchain_ollama.OllamaEmbeddings.  Expects settings to provide:   - embedding_model_name   - ollama_url (optional, if the client needs a custom endpoint)  Returns a langchain_core compatible Embeddings instance.
