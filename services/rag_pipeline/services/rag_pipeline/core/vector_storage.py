"""Vector Storage Manager for RAG Pipeline."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from qdrant_client import QdrantClient
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams,
    HnswConfigDiff,
)

from services.common.qdrant_client import QdrantClientSingleton

logger = logging.getLogger(__name__)


class VectorStorageManager:
    """Manages vector storage operations for RAG documents."""

    def __init__(
        self,
        url: str,
        collection_name: str,
        vector_size: int = 1536,
        use_singleton: bool = True,
        connection_pool_size: int = 20,
        timeout_seconds: int = 30,
    ):
        """Initialize vector storage manager.

        Args:
            url: Qdrant server URL
            collection_name: Name of the collection to use
            vector_size: Size of embedding vectors (default: 1536 for OpenAI)
            use_singleton: Whether to use singleton client (default: True)
            connection_pool_size: Size of connection pool for async operations
            timeout_seconds: Timeout for operations
        """
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.url = url
        self.connection_pool_size = connection_pool_size
        self.timeout_seconds = timeout_seconds

        # Initialize sync client for collection setup
        if use_singleton:
            self.client = QdrantClientSingleton(url).client
        else:
            self.client = QdrantClient(url=url)

        # Initialize async client pool
        self._async_client_pool = []
        self._pool_lock = asyncio.Lock()

        self._ensure_collection_exists()

    @asynccontextmanager
    async def _get_async_client(self):
        """Get async client from pool with connection management."""
        async with self._pool_lock:
            if self._async_client_pool:
                client = self._async_client_pool.pop()
            else:
                client = AsyncQdrantClient(
                    url=self.url,
                    timeout=self.timeout_seconds,
                    prefer_grpc=True,  # Better performance for high-throughput
                )

        try:
            yield client
        finally:
            async with self._pool_lock:
                if len(self._async_client_pool) < self.connection_pool_size:
                    self._async_client_pool.append(client)
                else:
                    await client.close()

    def _ensure_collection_exists(self):
        """Ensure the collection exists, create if not."""
        try:
            if not self.client.collection_exists(self.collection_name):
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size, distance=Distance.COSINE
                    ),
                    hnsw_config=HnswConfigDiff(
                        m=16, ef_construct=200, full_scan_threshold=10000
                    ),
                    optimizers_config={
                        "default_segment_number": 4,
                        "indexing_threshold": 10000,
                    },
                )
            else:
                # Get actual vector size from existing collection
                info = self.client.get_collection(self.collection_name)
                if hasattr(info.config.params, "vectors"):
                    self.vector_size = info.config.params.vectors.size
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise

    def add_documents(
        self, documents: List[Dict[str, Any]], embeddings: List[List[float]]
    ) -> Dict[str, int]:
        """Add documents with embeddings to vector storage.

        Args:
            documents: List of documents with id, content, and metadata
            embeddings: List of embedding vectors

        Returns:
            Dict with added and failed counts
        """
        if len(documents) != len(embeddings):
            raise ValueError("Documents and embeddings must have same length")

        try:
            points = []
            for doc, embedding in zip(documents, embeddings):
                point = PointStruct(
                    id=doc["id"],
                    vector=embedding,
                    payload={
                        "content": doc["content"],
                        "metadata": doc.get("metadata", {}),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
                points.append(point)

            self.client.upsert(collection_name=self.collection_name, points=points)

            return {"added": len(points), "failed": 0}

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise Exception(f"Failed to add documents: {str(e)}")

    async def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents asynchronously with connection pooling.

        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filters: Metadata filters

        Returns:
            List of search results with id, score, content, and metadata
        """
        search_params = SearchParams(
            hnsw_ef=min(256, limit * 4),  # Dynamic ef based on limit
            exact=False,
        )

        # Build query filter if provided
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(key=f"metadata.{key}", match=MatchValue(value=value))
                )
            if conditions:
                query_filter = Filter(must=conditions)

        async with self._get_async_client() as client:
            results = await client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True,
                search_params=search_params,
            )

        return [
            {
                "id": result.id,
                "score": result.score,
                "content": result.payload.get("content", ""),
                "metadata": result.payload.get("metadata", {}),
            }
            for result in results
        ]

    def hybrid_search(
        self,
        query_embedding: List[float],
        keywords: List[str],
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector and keyword search.

        Args:
            query_embedding: Query vector
            keywords: List of keywords to search
            vector_weight: Weight for vector similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
            limit: Maximum number of results

        Returns:
            List of re-ranked search results
        """
        # Get vector search results
        vector_results = self.search_similar(
            query_embedding=query_embedding,
            limit=limit * 2,  # Get more for re-ranking
        )

        # Score based on keyword matching
        results_with_scores = []
        for result in vector_results:
            content_lower = result["content"].lower()
            keyword_matches = sum(
                1 for keyword in keywords if keyword.lower() in content_lower
            )
            keyword_score = keyword_matches / len(keywords) if keywords else 0

            # Combine scores
            combined_score = (
                vector_weight * result["score"] + keyword_weight * keyword_score
            )

            results_with_scores.append(
                {
                    **result,
                    "vector_score": result["score"],
                    "keyword_score": keyword_score,
                    "score": combined_score,
                }
            )

        # Sort by combined score and return top results
        results_with_scores.sort(key=lambda x: x["score"], reverse=True)
        return results_with_scores[:limit]

    def delete_documents(self, doc_ids: List[str]) -> Dict[str, int]:
        """Delete documents by IDs.

        Args:
            doc_ids: List of document IDs to delete

        Returns:
            Dict with deleted count
        """
        try:
            self.client.delete(
                collection_name=self.collection_name, points_selector=doc_ids
            )
            return {"deleted": len(doc_ids)}
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics.

        Returns:
            Dict with collection stats
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
                "vector_size": self.vector_size,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise
