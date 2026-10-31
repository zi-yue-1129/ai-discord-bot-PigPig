# coding: utf-8
"""
Qdrant-based Vector Store using LangChain integration.
Simplified implementation using langchain-qdrant package.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, List, Optional, Tuple

from qdrant_client import QdrantClient

from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchText,
    PayloadSchemaType,
    TextIndexParams,
    TextIndexType,
    TokenizerType,
    VectorParams,
)
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from addons.settings import MemoryConfig
from addons.tokens import tokens
from cogs.memory.exceptions import VectorOperationError, SearchError
from cogs.memory.interfaces.vector_store_interface import MemoryFragment, VectorStoreInterface

logger = logging.getLogger(__name__)


class QdrantStore(VectorStoreInterface):
    """LangChain Qdrant vector store wrapper."""

    # Most words of one keyword query that are matched; the model sometimes sends very long ones.
    MAX_KEYWORD_QUERY_WORDS = 20

    # Payload indexes, on the paths the filters really use (the fields live under ``metadata``).
    # Keywords are stored as the summarizer wrote them (``HAREKAZE``, ``PigPig``), so the text index
    # lowercases both sides and a query matches whatever the letter case.
    PAYLOAD_INDEXES: List[Tuple[str, Any]] = [
        ("metadata.author_ids", PayloadSchemaType.KEYWORD),
        ("metadata.channel_id", PayloadSchemaType.KEYWORD),
        ("metadata.guild_id", PayloadSchemaType.KEYWORD),
        (
            "metadata.keywords",
            TextIndexParams(type=TextIndexType.TEXT, tokenizer=TokenizerType.WORD, lowercase=True, min_token_len=1),
        ),
    ]

    def __init__(self, settings: MemoryConfig, embedding_model: Optional[Embeddings]) -> None:
        if not embedding_model:
            raise VectorOperationError("Embedding model is required")

        qdrant_url = getattr(settings, "qdrant_url", None)
        collection_name = getattr(settings, "qdrant_collection_name", None)
        embedding_dim = getattr(settings, "embedding_dim", None)
        api_key = getattr(tokens, "vector_store_api_key", None)

        if not qdrant_url or not collection_name or not embedding_dim:
            raise VectorOperationError("Missing required Qdrant settings")

        self.settings = settings
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.embedding_dim = int(embedding_dim)

        try:
            self.client = QdrantClient(url=qdrant_url, api_key=api_key, timeout=60)
            # Log basic connection info (do not log api_key)
            logger.debug(
                "Qdrant client initialized (url=%s, collection=%s, embedding_dim=%d)",
                qdrant_url,
                self.collection_name,
                self.embedding_dim,
            )

            try:
                exists = self.client.collection_exists(self.collection_name)
                logger.debug("Qdrant collection exists=%s for %s", exists, self.collection_name)
                if not exists:
                    logger.info("Creating Qdrant collection: %s", self.collection_name)
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=self.embedding_dim,
                            distance=Distance.COSINE
                        ),
                    )
                    logger.info("Created Qdrant collection: %s", self.collection_name)
            except Exception as e:
                logger.exception("Failed while ensuring Qdrant collection exists")
                asyncio.create_task(self._report_error(e))
                raise VectorOperationError("Failed to ensure Qdrant collection") from e

            # Initialize LangChain QdrantVectorStore
            self.vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=self.collection_name,
                embedding=self.embedding_model,
            )
        except Exception as e:
            asyncio.create_task(self._report_error(e))
            raise VectorOperationError("Failed to initialize Qdrant") from e

    async def ensure_storage(self) -> None:
        """Ensure payload indexes exist.

        Collection creation is handled in __init__ to avoid langchain-qdrant
        raising 404 when the collection is missing during QdrantVectorStore init.
        """
        try:
            # Ensure collection exists before creating indexes; if not, log and return.
            if not self.client.collection_exists(self.collection_name):
                logger.warning(
                    "ensure_storage: collection %s does not exist; skipping index creation",
                    self.collection_name,
                )
                return

            # Create payload indexes for filtering (idempotent). One refused index must not
            # skip the others, but it is reported: searches still work without it, only slower
            # (or, for keywords, case-sensitive).
            for field_name, field_schema in self.PAYLOAD_INDEXES:
                try:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field_name,
                        field_schema=field_schema,
                    )
                except Exception as index_error:  # keep creating the other indexes; the failure is logged below
                    logger.error("Could not create payload index %s", field_name, exc_info=True)
                    asyncio.create_task(self._report_error(index_error))
        except Exception as e:
            asyncio.create_task(self._report_error(e))
            raise VectorOperationError("Failed to ensure storage") from e

    async def add_memories(self, memories: List[MemoryFragment]) -> None:
        """Add memories using LangChain's add_documents."""
        if not memories:
            return

        try:
            # Convert MemoryFragments to LangChain Documents
            documents = []
            for mem in memories:
                # Skip empty memories to prevent vector store errors
                if not mem.query_key or not mem.query_key.strip():
                    logger.warning("Skipping empty memory fragment: ID=%s", getattr(mem, "id", "unknown"))
                    continue

                metadata = getattr(mem, "metadata", {}) or {}
                if isinstance(metadata, dict):
                    # Ensure IDs are strings for filtering
                    if "author_ids" in metadata:
                        metadata["author_ids"] = [str(uid) for uid in metadata["author_ids"]] if isinstance(metadata["author_ids"], list) else [str(metadata["author_ids"])]
                    if "channel_id" in metadata:
                        metadata["channel_id"] = str(metadata["channel_id"])
                
                doc = Document(
                    page_content=mem.query_key,  # Embed query_key
                    metadata={
                        "summary": mem.content,
                        "fragment_id": getattr(mem, "id", ""),
                        **metadata
                    }
                )
                documents.append(doc)

            if not documents:
                logger.warning("No valid documents to add after filtering empty memories")
                return

            # Use LangChain's batch add
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.vector_store.add_documents(documents)
            )

        except Exception as e:
            asyncio.create_task(self._report_error(e))
            raise VectorOperationError("Failed to add memories") from e

    @staticmethod
    def _metadata_conditions(
        *, user_id: Optional[str], channel_id: Optional[str], guild_id: Optional[str]
    ) -> list:
        """Builds the payload filter conditions shared by vector and keyword search.

        Args:
            user_id: Only fragments this user took part in.
            channel_id: Only fragments from this channel.
            guild_id: Only fragments from this guild (keeps searches inside one server).

        Returns:
            Qdrant ``FieldCondition`` objects for the given limits.
        """
        from qdrant_client.models import FieldCondition, MatchAny, MatchValue

        conditions = []
        if user_id:
            conditions.append(FieldCondition(key="metadata.author_ids", match=MatchAny(any=[str(user_id)])))
        if channel_id:
            conditions.append(FieldCondition(key="metadata.channel_id", match=MatchValue(value=str(channel_id))))
        if guild_id:
            conditions.append(FieldCondition(key="metadata.guild_id", match=MatchValue(value=str(guild_id))))
        return conditions

    async def search_memories_by_vector(
        self,
        query_text: str,
        limit: int = 8,
        user_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        min_score: Optional[float] = None,
        guild_id: Optional[str] = None,
    ) -> List[MemoryFragment]:
        """Vector similarity search with metadata filtering."""
        try:
            from qdrant_client.models import FieldCondition, MatchAny, MatchValue, Filter
            
            filter_conditions = self._metadata_conditions(user_id=user_id, channel_id=channel_id, guild_id=guild_id)
            logger.info(f"🔍 Filter: user={user_id} channel={channel_id} guild={guild_id}")
            
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            loop = asyncio.get_event_loop()
            if search_filter:
                logger.info(f"🔍 Applying filter with {len(filter_conditions)} conditions")
                
                query_vector = await loop.run_in_executor(
                    None,
                    lambda: self.embedding_model.embed_query(query_text)
                )
                
                search_results = await loop.run_in_executor(
                    None,
                    lambda: self.client.search(
                        collection_name=self.collection_name,
                        query_vector=query_vector,
                        query_filter=search_filter,
                        limit=limit,
                        with_payload=True,
                        score_threshold=min_score
                    )
                )
                
                logger.info(f"✅ Found {len(search_results)} results with filter")
                
                results = []
                for scored_point in search_results:
                    payload = scored_point.payload or {}
                    metadata = payload.get("metadata", {})
                    
                    mem = MemoryFragment(
                        id=metadata.get("fragment_id", str(scored_point.id)),
                        content=metadata.get("summary", ""),
                        metadata=metadata,
                        query_key=payload.get("page_content", ""),
                        score=scored_point.score
                    )
                    results.append(mem)
                
                return results
            
            else:
                logger.info("🔍 No filter, using LangChain similarity_search")
                docs = await loop.run_in_executor(
                    None,
                    lambda: self.vector_store.similarity_search(query_text, k=limit)
                )
                
                results = []
                for doc in docs:
                    metadata = doc.metadata.copy()
                    summary = metadata.pop("summary", doc.page_content)
                    
                    mem = MemoryFragment(
                        id=metadata.get("fragment_id", ""),
                        content=summary,
                        metadata=metadata,
                        query_key=doc.page_content,
                        score=None
                    )
                    results.append(mem)
                
                logger.info(f"✅ Found {len(results)} results without filter")
                return results

        except Exception as e:
            logger.exception("❌ Vector search failed")
            asyncio.create_task(self._report_error(e))
            raise SearchError(f"Vector search failed: {str(e)}") from e


    async def sample_memories(
        self,
        guild_id: str,
        limit: int,
        channel_id: Optional[str] = None,
        since: Optional[float] = None,
    ) -> List[MemoryFragment]:
        """Returns up to ``limit`` random memories of one guild (for quiz questions).

        Args:
            guild_id: Only memories from this guild.
            limit: How many to return.
            channel_id: Only memories from this channel.
            since: Only memories that started at or after this UNIX time.
        """
        from qdrant_client.models import Range, Sample, SampleQuery

        conditions = self._metadata_conditions(user_id=None, channel_id=channel_id, guild_id=guild_id)
        if since is not None:
            conditions.append(FieldCondition(key="metadata.start_timestamp", range=Range(gte=float(since))))
        search_filter = Filter(must=conditions)
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.query_points(
                    collection_name=self.collection_name,
                    query=SampleQuery(sample=Sample.RANDOM),
                    limit=limit,
                    query_filter=search_filter,
                    with_payload=True,
                    with_vectors=False,
                ),
            )
        except Exception as e:
            logger.exception("Sampling memories failed")
            asyncio.create_task(self._report_error(e))
            raise SearchError(f"Sampling memories failed: {e}") from e
        fragments = []
        for point in result.points:
            payload = point.payload or {}
            metadata = payload.get("metadata", {})
            fragments.append(
                MemoryFragment(
                    id=metadata.get("fragment_id", str(point.id)),
                    content=metadata.get("summary", ""),
                    metadata=metadata,
                    query_key=payload.get("page_content", ""),
                )
            )
        return fragments

    @classmethod
    def _keyword_filter(cls, query_text: str) -> Optional[Filter]:
        """Builds the "any of these words" condition for a keyword search.

        Args:
            query_text: Words separated by whitespace.

        Returns:
            A filter matching fragments whose keywords contain any of the words (the text index
            ignores letter case), or ``None`` when the query has no words.
        """
        words = query_text.split()[: cls.MAX_KEYWORD_QUERY_WORDS]
        if not words:
            return None
        return Filter(should=[FieldCondition(key="metadata.keywords", match=MatchText(text=word)) for word in words])

    async def search_memories_by_keyword(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        k: int = 5,
        guild_id: Optional[str] = None,
    ) -> List[MemoryFragment]:
        """Keyword search using Qdrant query API with payload filtering."""
        try:
            
            # Build filter conditions: any query word may match a stored keyword
            filter_conditions = []
            keyword_filter = self._keyword_filter(query_text)
            if keyword_filter is not None:
                filter_conditions.append(keyword_filter)

            filter_conditions.extend(
                self._metadata_conditions(user_id=user_id, channel_id=channel_id, guild_id=guild_id)
            )

            # Create filter with all conditions
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Execute query search with filter
            loop = asyncio.get_event_loop()
            query_results = await loop.run_in_executor(
                None,
                lambda: self.client.query_points(
                    collection_name=self.collection_name,
                    query=[0.0] * self.embedding_dim,  # Zero vector for filtering only
                    limit=k,
                    query_filter=search_filter,
                    with_payload=True,
                    with_vectors=False
                )
            )
            
            # Convert Qdrant results to MemoryFragments
            results = []
            for point in query_results.points:
                payload = point.payload or {}
                metadata = payload.get("metadata", {})
                
                # Create MemoryFragment
                mem = MemoryFragment(
                    id=metadata.get("fragment_id", str(point.id)),
                    content=metadata.get("summary", ""),
                    metadata=metadata,
                    query_key=payload.get("page_content", ""),
                    score=point.score if hasattr(point, 'score') else None
                )
                results.append(mem)
            
            logger.info(f"✅ Keyword search returned {len(results)} results for query: {query_text}")
            return results
            
        except Exception as e:
            logger.exception("❌ Keyword search failed")
            asyncio.create_task(self._report_error(e))
            raise SearchError(f"Keyword search failed: {str(e)}") from e

    async def search(
        self,
        vector_query: Optional[str] = None,
        keyword_query: Optional[str] = None,
        user_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        guild_id: Optional[str] = None,
    ) -> List[MemoryFragment]:
        """Hybrid search combining vector and keyword results."""
        if not vector_query and not keyword_query:
            raise ValueError("At least one query type required")

        vector_k = getattr(self.settings, "vector_search_k", 5)
        keyword_k = getattr(self.settings, "keyword_search_k", 3)

        if vector_query and not keyword_query:
            return await self.search_memories_by_vector(
                vector_query, limit=vector_k, user_id=user_id, channel_id=channel_id, guild_id=guild_id
            )

        if keyword_query and not vector_query:
            return await self.search_memories_by_keyword(
                keyword_query, user_id=user_id, channel_id=channel_id, k=keyword_k, guild_id=guild_id
            )

        # Both queries: run in parallel and merge
        tasks = []
        if vector_query:
            tasks.append(self.search_memories_by_vector(
                vector_query, limit=vector_k, user_id=user_id, channel_id=channel_id, guild_id=guild_id
            ))
        if keyword_query:
            tasks.append(self.search_memories_by_keyword(
                keyword_query, user_id=user_id, channel_id=channel_id, k=keyword_k, guild_id=guild_id
            ))

        results = await asyncio.gather(*tasks)
        
        # Flatten results
        all_results = []
        for result_set in results:
            all_results.extend(result_set)

        # Deduplicate by fragment_id
        seen = set()
        merged = []
        for mem in all_results:
            frag_id = mem.metadata.get("fragment_id") or mem.id
            if frag_id not in seen:
                seen.add(frag_id)
                merged.append(mem)

        return merged

    async def delete_vectors_by_user(self, user_id: str) -> int:
        """Delete all vectors where user_id appears in metadata.author_ids."""
        from qdrant_client.models import Filter, FieldCondition, MatchAny, FilterSelector

        def _do_delete() -> int:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=FilterSelector(
                    filter=Filter(
                        must=[
                            FieldCondition(
                                key="metadata.author_ids",
                                match=MatchAny(any=[str(user_id)]),
                            )
                        ]
                    )
                ),
            )
            return -1  # Qdrant does not report deleted count

        try:
            return await asyncio.get_event_loop().run_in_executor(None, _do_delete)
        except Exception as e:
            await self._report_error(e)
            raise

    async def _report_error(self, error: Exception) -> None:
        """Helper to report errors."""
        try:
            from function import func
            await func.report_error(error)
        except Exception:
            logger.exception("Failed to report error")