# File: `cogs/memory/vector/manager.py`

## Overview
This file is part of the Discord bot commands and features (cogs) and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `cogs/memory/vector/manager.py`.

## Classes

### `VectorManager`
Factory class to dynamically initialize and provide a vector store instance and embedding model.  Responsibilities: - Manage an embedding provider registry (pluggable). - Initialize embedding model asynchronously based on settings. - Initialize vector store with dependency injection of the embedding model.

- **Attributes**:
  - `bot` (`Any`): Instance attribute bot
  - `settings` (`Any`): Instance attribute settings
  - `embedding_model` (`Optional[Embeddings]`): Instance attribute embedding_model
  - `_store` (`Optional[VectorStoreInterface]`): Instance attribute _store

- **Methods**:
  - `_get_store_class(self, store_type) -> Type[VectorStoreInterface]`: Dynamically imports and returns the vector store class from the 'vector_stores' directory.  Args:     store_type (str): The type of the vector store (e.g., "qdrant").  Returns:     Type[VectorStoreInterface]: The vector store class.  Raises:     ValueError: If the store class cannot be found or imported.
  - `_initialize_store(self) -> VectorStoreInterface`: Creates the configured VectorStore instance, injecting the embedding model.
  - `_initialize_embedding(self) -> Embeddings`: Initializes embedding model according to settings.embedding_provider.  This method looks up a provider in the registry and calls it with the MemoryConfig. The provider can be synchronous or asynchronous.  Raises:     ValueError: if provider not configured or provider not registered.
  - `initialize(self) -> Any`: Async initialization entrypoint.  1) Initialize embedding model 2) Initialize vector store with the embedding model injected 3) Call store.ensure_storage()
  - `store(self) -> VectorStoreInterface`: Provides public access to the vector store instance.
  - `get_embedding_model(self) -> Embeddings`: Return initialized embedding model synchronously (after initialize).
  - `set_embedding_model_for_tests(self, model) -> Any`: Method set_embedding_model_for_tests.

## Functions

### `register_embedding_provider(name) -> Any`
Decorator to register an embedding provider factory under a canonical name.  Example:     @register_embedding_provider("openai")     def openai_factory(settings: MemoryConfig) -> Embeddings:         ...
