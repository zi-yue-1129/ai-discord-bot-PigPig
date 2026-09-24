# File: `cogs/memory/vector/manager.py`

## Overview
Core file handling responsibilities within the `cogs/memory/vector` subsystem.

## Classes

### `VectorManager`
Factory class to dynamically initialize and provide a vector store instance and embedding model.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(bot: str, settings: str) -> Any`: Args:
  - `_get_store_class(store_type: str) -> Type[VectorStoreInterface]`: Dynamically imports and returns the vector store class from the 'vector_stores' directory.
  - `_initialize_store() -> VectorStoreInterface`: Creates the configured VectorStore instance, injecting the embedding model.
  - `_initialize_embedding() -> Embeddings`: Initializes embedding model according to settings.embedding_provider.
  - `initialize() -> Any`: Async initialization entrypoint.
  - `store() -> VectorStoreInterface`: Provides public access to the vector store instance.
  - `get_embedding_model() -> Embeddings`: Return initialized embedding model synchronously (after initialize).
  - `set_embedding_model_for_tests(model: Embeddings) -> Any`: No description provided.

## Functions

### `register_embedding_provider(name: str) -> Any`
Decorator to register an embedding provider factory under a canonical name.
