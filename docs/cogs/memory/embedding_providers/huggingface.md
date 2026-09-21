# File: `cogs/memory/embedding_providers/huggingface.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

No classes defined.

## Functions

### `huggingface_provider(settings: MemoryConfig) -> Embeddings`
Provider factory using langchain_huggingface.HuggingFaceEmbeddings.

Expects settings to provide:
  - embedding_model_name

Returns a langchain_core compatible Embeddings instance.
