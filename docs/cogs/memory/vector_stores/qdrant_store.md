# File: `cogs/memory/vector_stores/qdrant_store.py`

## Overview
Qdrant-based Vector Store using LangChain integration.
Simplified implementation using langchain-qdrant package.

## Classes

### `QdrantStore`
LangChain Qdrant vector store wrapper.

- **Attributes**:
  - `settings` (`Any`): Instance attribute for settings.
  - `embedding_model` (`Any`): Instance attribute for embedding_model.
  - `collection_name` (`Any`): Instance attribute for collection_name.
  - `embedding_dim` (`Any`): Instance attribute for embedding_dim.

- **Methods**:
  - `__init__(settings, embedding_model) -> None`: Handles the `__init__` functionality. Internally, it interacts with methods like `VectorOperationError` and `QdrantClient`.
  - `ensure_storage() -> None`: Ensure payload indexes exist.
  - `add_memories(memories) -> None`: Add memories using LangChain's add_documents.
  - `search_memories_by_vector(query_text, limit, user_id, channel_id, min_score) -> List[...]`: Vector similarity search with metadata filtering.
  - `search_memories_by_keyword(query_text, user_id, channel_id, k) -> List[...]`: Keyword search using Qdrant query API with payload filtering.
  - `search(vector_query, keyword_query, user_id, channel_id) -> List[...]`: Hybrid search combining vector and keyword results.
  - `delete_vectors_by_user(user_id) -> int`: Delete all vectors where user_id appears in metadata.author_ids.
  - `_report_error(error) -> None`: Helper to report errors.
