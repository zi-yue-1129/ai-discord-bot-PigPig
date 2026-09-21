# File: `cogs/memory/vector_stores/qdrant_store.py`

## Overview
Qdrant-based Vector Store using LangChain integration.
Simplified implementation using langchain-qdrant package.

## Classes

### `QdrantStore`
LangChain Qdrant vector store wrapper.

- **Attributes**:
  - `settings` (`Any`): Attribute holding settings data.
  - `embedding_model` (`Any`): Attribute holding embedding_model data.
  - `collection_name` (`Any`): Attribute holding collection_name data.
  - `embedding_dim` (`Any`): Attribute holding embedding_dim data.

- **Methods**:
  - `__init__(settings: MemoryConfig, embedding_model: Optional[Embeddings]) -> None`: Executes __init__ logic.
  - `ensure_storage() -> None`: Ensure payload indexes exist.
  - `add_memories(memories: List[MemoryFragment]) -> None`: Add memories using LangChain's add_documents.
  - `search_memories_by_vector(query_text: str, limit: int, user_id: Optional[str], channel_id: Optional[str], min_score: Optional[float]) -> List[MemoryFragment]`: Vector similarity search with metadata filtering.
  - `search_memories_by_keyword(query_text: str, user_id: Optional[str], channel_id: Optional[str], k: int) -> List[MemoryFragment]`: Keyword search using Qdrant query API with payload filtering.
  - `search(vector_query: Optional[str], keyword_query: Optional[str], user_id: Optional[str], channel_id: Optional[str]) -> List[MemoryFragment]`: Hybrid search combining vector and keyword results.
  - `delete_vectors_by_user(user_id: str) -> int`: Delete all vectors where user_id appears in metadata.author_ids.
  - `_report_error(error: Exception) -> None`: Helper to report errors.

## Functions

No top-level functions defined.
