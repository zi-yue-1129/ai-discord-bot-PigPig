# File: `cogs/memory/vector/manager.py`

## Overview
This file is part of the `cogs` subsystem. It is responsible for `manager` related functionality within the PigPig system, contributing to Discord bot commands and feature logic.

## Classes

### `VectorManager`
Factory class to dynamically initialize and provide a vector store instance and embedding model.

Responsibilities:
- Manage an embedding provider registry (pluggable).
- Initialize embedding model asynchronously based on settings.
- Initialize vector store with dependency injection of the embedding model.

- **Attributes**:
  - `bot` (`Any`): Instance attribute for bot.
  - `settings` (`Any`): Instance attribute for settings.
  - `embedding_model` (`Optional[...]`): Instance attribute for embedding_model.
  - `_store` (`Optional[...]`): Instance attribute for _store.

- **Methods**:
  - `__init__(bot, settings) -> Any`: Args:
  - `_get_store_class(store_type) -> Type[...]`: Dynamically imports and returns the vector store class from the 'vector_stores' directory.
  - `_initialize_store() -> VectorStoreInterface`: Creates the configured VectorStore instance, injecting the embedding model.
  - `_initialize_embedding() -> Embeddings`: Initializes embedding model according to settings.embedding_provider.
  - `initialize() -> Any`: Async initialization entrypoint.
  - `store() -> VectorStoreInterface`: Provides public access to the vector store instance.
  - `get_embedding_model() -> Embeddings`: Return initialized embedding model synchronously (after initialize).
  - `set_embedding_model_for_tests(model) -> Any`: Handles the `set_embedding_model_for_tests` functionality. Internally, it interacts with methods like `_initialize_store`.

## Functions

### `register_embedding_provider(name) -> Any`
Decorator to register an embedding provider factory under a canonical name.
