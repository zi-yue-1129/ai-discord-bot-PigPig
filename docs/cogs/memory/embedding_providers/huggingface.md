# File: `cogs/memory/embedding_providers/huggingface.py`

## Overview
Core logic and functionalities for huggingface.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Functions

### `huggingface_provider(settings) -> Embeddings`
Provider factory using langchain_huggingface.HuggingFaceEmbeddings.

Expects settings to provide:
  - embedding_model_name

Returns a langchain_core compatible Embeddings instance.
