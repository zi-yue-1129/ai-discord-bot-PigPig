# File: `cogs/memory/vector_stores/qdrant_store.py`

## Overview
Qdrant-based Vector Store using LangChain integration.
Simplified implementation using langchain-qdrant package.

## Classes

### `QdrantStore`
LangChain Qdrant vector store wrapper.

- **Attributes**:
  - `settings` (`Any`): Instance attribute managing settings.
  - `embedding_model` (`Any`): Instance attribute managing embedding_model.
  - `collection_name` (`Any`): Instance attribute managing collection_name.
  - `embedding_dim` (`Any`): Instance attribute managing embedding_dim.

- **Methods**:
  - `ensure_storage() -> None`: Ensure payload indexes exist.  Collection creation is handled in __init__ to avoid langchain-qdrant raising 404 when the collection is missing during QdrantVectorStore init.
  - `add_memories(memories) -> None`: Add memories using LangChain's add_documents.
  - `search_memories_by_vector(query_text, limit, user_id, channel_id, min_score) -> List[MemoryFragment]`: Vector similarity search with metadata filtering.
  - `search_memories_by_keyword(query_text, user_id, channel_id, k) -> List[MemoryFragment]`: Keyword search using Qdrant query API with payload filtering.
  - `search(vector_query, keyword_query, user_id, channel_id) -> List[MemoryFragment]`: Hybrid search combining vector and keyword results.
  - `delete_vectors_by_user(user_id) -> int`: Delete all vectors where user_id appears in metadata.author_ids.
