"""Multi-stage Retrieval Pipeline with re-ranking."""

import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import numpy as np
from sentence_transformers import CrossEncoder

from services.rag_pipeline.core.vector_storage import VectorStorageManager
from services.rag_pipeline.core.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class RetrievalConfig:
    """Configuration for retrieval pipeline."""

    top_k: int = 10
    rerank_top_k: int = 5
    min_relevance_score: float = 0.7
    use_mmr: bool = True  # Maximal Marginal Relevance
    mmr_lambda: float = 0.5
    similarity_threshold: float = 0.85


@dataclass
class RetrievalResult:
    """Result from retrieval pipeline."""

    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    enhanced_content: Optional[str] = None
    rerank_score: Optional[float] = None


class ReRanker:
    """Cross-encoder based re-ranker for retrieval results."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Initialize re-ranker with cross-encoder model."""
        self.model = CrossEncoder(model_name)

    def rerank(
        self, query: str, documents: List[Dict[str, Any]], top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Re-rank documents based on query.

        Args:
            query: Search query
            documents: List of documents to re-rank
            top_k: Number of top documents to return

        Returns:
            Re-ranked documents
        """
        if not documents:
            return []

        # Prepare pairs for cross-encoder
        pairs = [[query, doc["content"]] for doc in documents]

        # Get cross-encoder scores
        scores = self.model.predict(pairs)

        # Add scores to documents
        for doc, score in zip(documents, scores):
            doc["rerank_score"] = float(score)

        # Sort by re-rank score
        reranked = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)

        # Return top_k if specified
        if top_k:
            reranked = reranked[:top_k]

        return reranked


class RetrievalPipeline:
    """Multi-stage retrieval pipeline for RAG."""

    def __init__(
        self,
        vector_storage: VectorStorageManager,
        embedding_service: EmbeddingService,
        reranker: Optional[ReRanker] = None,
        config: Optional[RetrievalConfig] = None,
    ):
        """Initialize retrieval pipeline.

        Args:
            vector_storage: Vector storage manager
            embedding_service: Embedding service
            reranker: Optional re-ranker
            config: Retrieval configuration
        """
        self.vector_storage = vector_storage
        self.embedding_service = embedding_service
        self.reranker = reranker or ReRanker()
        self.config = config or RetrievalConfig()

        # Metrics tracking
        self._metrics = {"total_queries": 0, "total_latency_ms": 0, "total_results": 0}

    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        mode: str = "vector",  # vector, hybrid
        use_reranking: bool = False,
        enhance_context: bool = False,
        use_multi_query: bool = False,
    ) -> List[RetrievalResult]:
        """Retrieve relevant documents for query.

        Args:
            query: Search query
            filters: Metadata filters
            mode: Retrieval mode (vector or hybrid)
            use_reranking: Whether to use re-ranking
            enhance_context: Whether to enhance context
            use_multi_query: Whether to use query expansion

        Returns:
            List of retrieval results
        """
        start_time = time.time()

        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            # Query expansion if requested
            queries = [query]
            if use_multi_query:
                queries.extend(await self._generate_multi_queries(query))

            # Retrieve for all queries
            all_results = []
            for q in queries:
                if mode == "hybrid":
                    results = await self._hybrid_retrieve(q, filters)
                else:
                    results = await self._vector_retrieve(q, filters)
                all_results.extend(results)

            # Deduplicate and merge results
            results = self._deduplicate_results(all_results)

            # Apply minimum score filter
            results = [
                r for r in results if r["score"] >= self.config.min_relevance_score
            ]

            # Re-rank if requested
            if use_reranking and self.reranker and results:
                results = self.reranker.rerank(
                    query, results, top_k=self.config.rerank_top_k
                )

            # Apply MMR for diversity
            if self.config.use_mmr and len(results) > 1:
                results = await self._apply_mmr(query, results)

            # Enhance context if requested
            if enhance_context:
                results = await self._enhance_context(results)

            # Convert to RetrievalResult objects
            retrieval_results = [
                RetrievalResult(
                    id=r["id"],
                    content=r["content"],
                    score=r["score"],
                    metadata=r.get("metadata", {}),
                    enhanced_content=r.get("enhanced_content"),
                    rerank_score=r.get("rerank_score"),
                )
                for r in results[: self.config.top_k]
            ]

            # Update metrics
            elapsed_ms = (time.time() - start_time) * 1000
            self._update_metrics(elapsed_ms, len(retrieval_results))

            return retrieval_results

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            raise

    async def _vector_retrieve(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)

        # Search similar documents
        results = self.vector_storage.search_similar(
            query_embedding=query_embedding,
            limit=self.config.top_k * 2,  # Get more for filtering
            filters=filters,
        )

        return results

    async def _hybrid_retrieve(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector and keyword search."""
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)

        # Extract keywords from query
        keywords = self._extract_keywords(query)

        # Perform hybrid search
        results = self.vector_storage.hybrid_search(
            query_embedding=query_embedding,
            keywords=keywords,
            limit=self.config.top_k * 2,
        )

        return results

    async def _generate_multi_queries(self, query: str) -> List[str]:
        """Generate multiple query variations for better recall."""
        # Simple query expansion - in production, use LLM
        variations = []

        # Add question variation
        if not query.endswith("?"):
            variations.append(f"What is {query}?")

        # Add context variation
        variations.append(f"Explain {query} in detail")

        # Add related variation
        variations.append(f"Information about {query}")

        return variations[:2]  # Limit to avoid too many queries

    def _deduplicate_results(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Deduplicate results based on content similarity."""
        if not results:
            return []

        unique_results = []
        seen_ids = set()

        for result in results:
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                unique_results.append(result)

        # Sort by score
        unique_results.sort(key=lambda x: x["score"], reverse=True)

        return unique_results

    async def _apply_mmr(
        self, query: str, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply Maximal Marginal Relevance for diversity with memory optimization."""
        if len(results) <= 1:
            return results

        # Memory optimization: limit candidates and use streaming
        max_candidates = min(len(results), 50)  # Limit memory usage
        candidate_results = results[:max_candidates]

        # Get embeddings for candidates only
        contents = [r["content"] for r in candidate_results]

        # Batch embeddings with memory-efficient processing
        embeddings = await self.embedding_service.embed_batch(contents)

        # Get query embedding (cached)
        query_embedding = await self.embedding_service.embed_text(query)

        # Pre-calculate relevance scores to avoid repeated computation
        relevance_scores = [
            self._cosine_similarity(query_embedding, emb) for emb in embeddings
        ]

        # MMR algorithm with optimized similarity computation
        selected = []
        selected_indices = set()
        selected_embeddings = []  # Cache selected embeddings

        # Select first document (highest relevance)
        best_idx = max(range(len(relevance_scores)), key=lambda i: relevance_scores[i])
        selected.append(candidate_results[best_idx])
        selected_indices.add(best_idx)
        selected_embeddings.append(embeddings[best_idx])

        # Select remaining documents
        target_count = min(self.config.top_k, len(candidate_results))
        while len(selected) < target_count:
            best_score = -1
            best_idx = -1

            for i in range(len(candidate_results)):
                if i in selected_indices:
                    continue

                # Use pre-calculated relevance
                relevance = relevance_scores[i]

                # Calculate similarity to selected documents (optimized)
                max_sim = 0
                for selected_emb in selected_embeddings:
                    sim = self._cosine_similarity(embeddings[i], selected_emb)
                    max_sim = max(max_sim, sim)

                # MMR score
                mmr_score = (
                    self.config.mmr_lambda * relevance
                    - (1 - self.config.mmr_lambda) * max_sim
                )

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i

            if best_idx >= 0:
                selected.append(candidate_results[best_idx])
                selected_indices.add(best_idx)
                selected_embeddings.append(embeddings[best_idx])
            else:
                break

        return selected

    async def _enhance_context(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enhance context of retrieved documents."""
        for result in results:
            # Add surrounding context information
            enhanced = f"Document ID: {result['id']}\n"
            enhanced += f"Relevance Score: {result['score']:.3f}\n"
            enhanced += f"Content: {result['content']}\n"

            if result.get("metadata"):
                enhanced += f"Source: {result['metadata'].get('source', 'Unknown')}\n"

            result["enhanced_content"] = enhanced

        return results

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query."""
        # Simple keyword extraction - in production, use NLP
        stopwords = {"the", "is", "at", "which", "on", "a", "an", "and", "or", "but"}
        words = query.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        return keywords

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)

        if norm_product == 0:
            return 0.0

        return dot_product / norm_product

    def _update_metrics(self, latency_ms: float, result_count: int):
        """Update retrieval metrics."""
        self._metrics["total_queries"] += 1
        self._metrics["total_latency_ms"] += latency_ms
        self._metrics["total_results"] += result_count

    def get_metrics(self) -> Dict[str, Any]:
        """Get retrieval metrics."""
        total_queries = self._metrics["total_queries"]

        if total_queries == 0:
            return {"total_queries": 0, "avg_latency_ms": 0, "avg_results_per_query": 0}

        return {
            "total_queries": total_queries,
            "avg_latency_ms": self._metrics["total_latency_ms"] / total_queries,
            "avg_results_per_query": self._metrics["total_results"] / total_queries,
        }
