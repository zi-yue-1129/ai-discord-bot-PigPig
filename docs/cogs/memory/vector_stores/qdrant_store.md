# File: `cogs/memory/vector_stores/qdrant_store.py`

## Overview
Qdrant-based Vector Store using LangChain integration.
Simplified implementation using langchain-qdrant package.

## Classes

### `QdrantStore`
LangChain Qdrant vector store wrapper.

- **Attributes**:
  - `settings` (`Any`): Instance attribute settings
  - `embedding_model` (`Any`): Instance attribute embedding_model
  - `collection_name` (`Any`): Instance attribute collection_name
  - `embedding_dim` (`Any`): Instance attribute embedding_dim
  - `client` (`Any`): Instance attribute client
  - `vector_store` (`Any`): Instance attribute vector_store

- **Methods**:
  - `ensure_storage(self) -> None`: Ensure payload indexes exist.  Collection creation is handled in __init__ to avoid langchain-qdrant raising 404 when the collection is missing during QdrantVectorStore init.
  - `add_memories(self, memories) -> None`: Add memories using LangChain's add_documents.
  - `search_memories_by_vector(self, query_text, limit, user_id, channel_id, min_score) -> List[MemoryFragment]`: Vector similarity search with metadata filtering.
  - `search_memories_by_keyword(self, query_text, user_id, channel_id, k) -> List[MemoryFragment]`: Keyword search using Qdrant query API with payload filtering.
  - `search(self, vector_query, keyword_query, user_id, channel_id) -> List[MemoryFragment]`: Hybrid search combining vector and keyword results.
  - `delete_vectors_by_user(self, user_id) -> int`: Delete all vectors where user_id appears in metadata.author_ids.
  - `_report_error(self, error) -> None`: Helper to report errors.

## Functions

None
