# File: `cogs/memory/vector/manager.py`

## Overview
Core logic and functionalities for manager.py. This file is part of the cogs subsystem and handles the primary operations for its respective domain.

## Classes

### `VectorManager`
Factory class to dynamically initialize and provide a vector store instance and embedding model.

Responsibilities:
- Manage an embedding provider registry (pluggable).
- Initialize embedding model asynchronously based on settings.
- Initialize vector store with dependency injection of the embedding model.

- **Attributes**:
  - `bot` (`Any`): Instance attribute managing bot.
  - `settings` (`Any`): Instance attribute managing settings.

- **Methods**:
  - `initialize() -> Any`: Async initialization entrypoint.  1) Initialize embedding model 2) Initialize vector store with the embedding model injected 3) Call store.ensure_storage()
  - `store() -> VectorStoreInterface`: Provides public access to the vector store instance.
  - `get_embedding_model() -> Embeddings`: Return initialized embedding model synchronously (after initialize).
  - `set_embedding_model_for_tests(model) -> Any`: Executes set_embedding_model_for_tests operation.

## Functions

### `register_embedding_provider(name) -> Any`
Decorator to register an embedding provider factory under a canonical name.

Example:
    @register_embedding_provider("openai")
    def openai_factory(settings: MemoryConfig) -> Embeddings:
        ...
