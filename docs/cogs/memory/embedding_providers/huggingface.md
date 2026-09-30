# File: `cogs/memory/embedding_providers/huggingface.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/memory/embedding_providers/huggingface.py`.

## Classes

None

## Functions

### `huggingface_provider(settings) -> Embeddings`
Provider factory using langchain_huggingface.HuggingFaceEmbeddings.  Expects settings to provide:   - embedding_model_name  Returns a langchain_core compatible Embeddings instance.
