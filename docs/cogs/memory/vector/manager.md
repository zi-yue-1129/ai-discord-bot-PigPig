# File: `cogs/memory/vector/manager.py`

## Overview
This file is part of the cogs subsystem. It provides core functionality and logic for its respective domain within the PigPig project.

## Classes

### `VectorManager`
Factory class to dynamically initialize and provide a vector store instance and embedding model.

Responsibilities:
- Manage an embedding provider registry (pluggable).
- Initialize embedding model asynchronously based on settings.
- Initialize vector store with dependency injection of the embedding model.

- **Attributes**:
  - `bot` (`Any`): Attribute holding bot data.
  - `settings` (`Any`): Attribute holding settings data.
  - `embedding_model` (`Optional[Embeddings]`): Attribute holding embedding_model data.
  - `_store` (`Optional[VectorStoreInterface]`): Attribute holding _store data.

- **Methods**:
  - `__init__(bot: Bot, settings: MemoryConfig) -> Any`: Args:
  - `_get_store_class(store_type: str) -> Type[VectorStoreInterface]`: Dynamically imports and returns the vector store class from the 'vector_stores' directory.
  - `_initialize_store() -> VectorStoreInterface`: Creates the configured VectorStore instance, injecting the embedding model.
  - `_initialize_embedding() -> Embeddings`: Initializes embedding model according to settings.embedding_provider.
  - `initialize() -> Any`: Async initialization entrypoint.
  - `store() -> VectorStoreInterface`: Provides public access to the vector store instance.
  - `get_embedding_model() -> Embeddings`: Return initialized embedding model synchronously (after initialize).
  - `set_embedding_model_for_tests(model: Embeddings) -> Any`: Executes set_embedding_model_for_tests logic.

## Functions

### `register_embedding_provider(name: str) -> Any`
Decorator to register an embedding provider factory under a canonical name.

Example:
    @register_embedding_provider("openai")
    def openai_factory(settings: MemoryConfig) -> Embeddings:
        ...
