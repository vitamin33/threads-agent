"""API routes for RAG pipeline operations."""

import time
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from services.rag_pipeline.main import (
    get_vector_storage,
    get_embedding_service,
    get_retrieval_pipeline,
    rag_requests,
    rag_latency,
)
from services.rag_pipeline.processing.document_processor import (
    DocumentProcessor,
    ChunkingStrategy,
)
from services.rag_pipeline.evaluation.rag_evaluator import RAGEvaluator
from services.rag_pipeline.evaluation.monitoring import RAGQualityMonitor

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class Document(BaseModel):
    """Document for ingestion."""

    id: str = Field(..., description="Unique document ID")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )


class IngestRequest(BaseModel):
    """Request for document ingestion."""

    documents: List[Document] = Field(..., description="Documents to ingest")
    chunk_size: int = Field(default=1000, description="Chunk size for splitting")
    chunk_overlap: int = Field(default=100, description="Overlap between chunks")
    strategy: str = Field(default="recursive", description="Chunking strategy")


class IngestResponse(BaseModel):
    """Response from document ingestion."""

    ingested_documents: int
    total_chunks: int
    failed_documents: List[str]
    elapsed_seconds: float


class SearchRequest(BaseModel):
    """Request for search/retrieval."""

    query: str = Field(..., description="Search query")
    top_k: int = Field(default=10, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Metadata filters"
    )
    mode: str = Field(default="vector", description="Search mode: vector or hybrid")
    use_reranking: bool = Field(default=False, description="Use re-ranking")
    enhance_context: bool = Field(default=False, description="Enhance result context")


class SearchResult(BaseModel):
    """Search result."""

    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    enhanced_content: Optional[str] = None
    rerank_score: Optional[float] = None


class SearchResponse(BaseModel):
    """Response from search."""

    query: str
    results: List[SearchResult]
    total_results: int
    elapsed_seconds: float


class DeleteRequest(BaseModel):
    """Request for document deletion."""

    document_ids: List[str] = Field(..., description="Document IDs to delete")


class StatsResponse(BaseModel):
    """Statistics response."""

    total_documents: int
    total_vectors: int
    collection_status: str
    vector_dimension: int
    retrieval_metrics: Dict[str, Any]


class EvaluationRequest(BaseModel):
    """Request for RAG evaluation."""

    query: str = Field(..., description="Query to evaluate")
    context: List[str] = Field(..., description="Retrieved context")
    generated_answer: str = Field(..., description="Generated answer")
    reference_answer: Optional[str] = Field(
        default=None, description="Reference answer for comparison"
    )
    retrieved_docs: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Retrieved documents"
    )


class EvaluationResponse(BaseModel):
    """Response from RAG evaluation."""

    query: str
    answer_metrics: Dict[str, Any]
    retrieval_metrics: Optional[Dict[str, Any]]
    overall_score: float
    alerts: List[Dict[str, Any]]
    evaluation_latency_ms: float


class BatchEvaluationRequest(BaseModel):
    """Request for batch evaluation."""

    test_cases: List[EvaluationRequest] = Field(
        ..., description="List of test cases to evaluate"
    )


class QualityTrendsResponse(BaseModel):
    """Response for quality trends."""

    period_hours: int
    total_evaluations: int
    avg_overall_score: float
    min_overall_score: float
    max_overall_score: float
    score_trend: str


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    vector_storage=Depends(get_vector_storage),
    embedding_service=Depends(get_embedding_service),
):
    """Ingest documents into the RAG pipeline."""
    start_time = time.time()

    try:
        # Initialize document processor
        strategy_map = {
            "recursive": ChunkingStrategy.RECURSIVE,
            "semantic": ChunkingStrategy.SEMANTIC,
            "sliding_window": ChunkingStrategy.SLIDING_WINDOW,
            "markdown": ChunkingStrategy.MARKDOWN,
        }

        processor = DocumentProcessor(
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            strategy=strategy_map.get(request.strategy, ChunkingStrategy.RECURSIVE),
        )

        # Process documents
        all_chunks = []
        failed_documents = []

        for doc in request.documents:
            try:
                # Process document into chunks
                chunks = processor.process_text(
                    text=doc.content,
                    metadata={
                        **doc.metadata,
                        "doc_id": doc.id,
                        "ingested_at": datetime.utcnow().isoformat(),
                    },
                    enrich_metadata=True,
                )

                # Convert chunks for storage
                for chunk in chunks:
                    all_chunks.append(
                        {
                            "id": chunk.chunk_id,
                            "content": chunk.content,
                            "metadata": chunk.metadata,
                        }
                    )

            except Exception as e:
                logger.error(f"Failed to process document {doc.id}: {e}")
                failed_documents.append(doc.id)

        # Generate embeddings and store in optimized batches
        if all_chunks:
            chunk_texts = [c["content"] for c in all_chunks]

            # Process in optimal batches for memory efficiency
            batch_size = 50  # Optimal for memory/performance balance
            total_added = 0
            total_failed = 0

            for i in range(0, len(all_chunks), batch_size):
                batch_end = min(i + batch_size, len(all_chunks))
                batch_chunks = all_chunks[i:batch_end]
                batch_texts = chunk_texts[i:batch_end]

                try:
                    # Generate embeddings for batch
                    batch_embeddings = await embedding_service.embed_batch(batch_texts)

                    # Add batch to vector storage
                    batch_result = vector_storage.add_documents(
                        batch_chunks, batch_embeddings
                    )
                    total_added += batch_result.get("added", 0)
                    total_failed += batch_result.get("failed", 0)

                except Exception as e:
                    logger.error(f"Failed to process batch {i}-{batch_end}: {e}")
                    total_failed += len(batch_chunks)

            # Track metrics
            rag_requests.labels(operation="ingest", status="success").inc()
        else:
            pass  # No documents provided

        elapsed = time.time() - start_time
        rag_latency.labels(operation="ingest").observe(elapsed)

        return IngestResponse(
            ingested_documents=len(request.documents) - len(failed_documents),
            total_chunks=len(all_chunks),
            failed_documents=failed_documents,
            elapsed_seconds=elapsed,
        )

    except Exception as e:
        rag_requests.labels(operation="ingest", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest, retrieval_pipeline=Depends(get_retrieval_pipeline)
):
    """Search for relevant documents using optimized async pipeline."""
    start_time = time.time()

    try:
        # Validate request parameters
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        if request.top_k <= 0 or request.top_k > 100:
            raise HTTPException(
                status_code=400, detail="top_k must be between 1 and 100"
            )

        # Perform retrieval with timeout protection
        retrieval_task = retrieval_pipeline.retrieve(
            query=request.query,
            filters=request.filters,
            mode=request.mode,
            use_reranking=request.use_reranking,
            enhance_context=request.enhance_context,
        )

        # Add timeout to prevent hanging requests
        results = await asyncio.wait_for(retrieval_task, timeout=30.0)

        # Convert to response format
        search_results = [
            SearchResult(
                id=r.id,
                content=r.content,
                score=r.score,
                metadata=r.metadata,
                enhanced_content=r.enhanced_content,
                rerank_score=r.rerank_score,
            )
            for r in results[: request.top_k]
        ]

        elapsed = time.time() - start_time

        # Track metrics
        rag_requests.labels(operation="search", status="success").inc()
        rag_latency.labels(operation="search").observe(elapsed)

        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            elapsed_seconds=elapsed,
        )

    except Exception as e:
        rag_requests.labels(operation="search", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents")
async def delete_documents(
    request: DeleteRequest, vector_storage=Depends(get_vector_storage)
):
    """Delete documents from the RAG pipeline."""
    try:
        result = vector_storage.delete_documents(request.document_ids)

        rag_requests.labels(operation="delete", status="success").inc()

        return {"deleted": result["deleted"], "document_ids": request.document_ids}

    except Exception as e:
        rag_requests.labels(operation="delete", status="error").inc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_statistics(
    vector_storage=Depends(get_vector_storage),
    retrieval_pipeline=Depends(get_retrieval_pipeline),
):
    """Get RAG pipeline statistics."""
    try:
        # Get vector storage stats
        storage_stats = vector_storage.get_collection_stats()

        # Get retrieval metrics
        retrieval_metrics = retrieval_pipeline.get_metrics()

        return StatsResponse(
            total_documents=storage_stats["points_count"],
            total_vectors=storage_stats["vectors_count"],
            collection_status=storage_stats["status"],
            vector_dimension=storage_stats["vector_size"],
            retrieval_metrics=retrieval_metrics,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex")
async def reindex_collection(
    background_tasks: BackgroundTasks, vector_storage=Depends(get_vector_storage)
):
    """Trigger collection reindexing for optimization."""
    try:
        # This would trigger a background reindexing job
        # For now, just return acknowledgment

        return {
            "status": "reindexing_started",
            "message": "Collection reindexing has been triggered",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_rag_quality(
    request: EvaluationRequest, embedding_service=Depends(get_embedding_service)
):
    """Evaluate RAG quality for a single query-answer pair."""
    start_time = time.time()

    try:
        # Initialize evaluator
        evaluator = RAGEvaluator(embedding_service=embedding_service)

        # Initialize monitor (without Redis for now)
        monitor = RAGQualityMonitor(evaluator=evaluator)

        # Monitor query quality
        result = await monitor.monitor_query(
            query=request.query,
            context=request.context,
            generated_answer=request.generated_answer,
            reference_answer=request.reference_answer,
            retrieved_docs=request.retrieved_docs,
        )

        elapsed = time.time() - start_time

        return EvaluationResponse(
            query=result["query"],
            answer_metrics=result["answer_metrics"],
            retrieval_metrics=result.get("retrieval_metrics"),
            overall_score=result["overall_score"],
            alerts=result.get("alerts", []),
            evaluation_latency_ms=elapsed * 1000,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate/batch")
async def batch_evaluate_rag_quality(
    request: BatchEvaluationRequest, embedding_service=Depends(get_embedding_service)
):
    """Evaluate RAG quality for multiple query-answer pairs."""
    try:
        # Initialize evaluator
        evaluator = RAGEvaluator(embedding_service=embedding_service)

        # Convert test cases
        test_cases = []
        for case in request.test_cases:
            test_cases.append(
                {
                    "query": case.query,
                    "context": case.context,
                    "generated_answer": case.generated_answer,
                    "reference_answer": case.reference_answer,
                    "retrieved_docs": case.retrieved_docs,
                }
            )

        # Batch evaluate
        results = await evaluator.batch_evaluate(test_cases)

        # Calculate aggregate metrics
        aggregate_metrics = evaluator.get_aggregate_metrics(results)

        return {
            "results": results,
            "aggregate_metrics": aggregate_metrics,
            "total_cases": len(test_cases),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/trends")
async def get_quality_trends(
    hours: int = 24, embedding_service=Depends(get_embedding_service)
):
    """Get RAG quality trends over time."""
    try:
        # Initialize evaluator and monitor
        evaluator = RAGEvaluator(embedding_service=embedding_service)
        monitor = RAGQualityMonitor(evaluator=evaluator)

        # Get trends
        trends = await monitor.get_quality_trends(hours=hours)

        return trends

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/alerts")
async def get_active_alerts(embedding_service=Depends(get_embedding_service)):
    """Get currently active quality alerts."""
    try:
        # Initialize evaluator and monitor
        evaluator = RAGEvaluator(embedding_service=embedding_service)
        monitor = RAGQualityMonitor(evaluator=evaluator)

        # Get active alerts
        alerts = await monitor.get_active_alerts()

        return {"active_alerts": alerts, "total_alerts": len(alerts)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quality/benchmark")
async def run_quality_benchmark(
    background_tasks: BackgroundTasks, embedding_service=Depends(get_embedding_service)
):
    """Run comprehensive quality benchmark."""
    try:
        # Define benchmark test cases
        benchmark_cases = [
            {
                "query": "What is machine learning?",
                "context": [
                    "Machine learning is a subset of artificial intelligence",
                    "It focuses on algorithms that can learn from data",
                ],
                "generated_answer": "Machine learning is a subset of AI that uses algorithms to learn from data",
                "reference_answer": "Machine learning is a branch of AI that enables computers to learn from data",
            },
            {
                "query": "How does deep learning work?",
                "context": [
                    "Deep learning uses neural networks with multiple layers",
                    "Each layer learns increasingly complex features",
                ],
                "generated_answer": "Deep learning works by using multi-layer neural networks to learn complex patterns",
                "reference_answer": "Deep learning uses neural networks with many layers to learn hierarchical representations",
            },
        ]

        # Initialize evaluator
        evaluator = RAGEvaluator(embedding_service=embedding_service)

        # Run benchmark in background
        async def run_benchmark():
            results = await evaluator.batch_evaluate(benchmark_cases)
            aggregate = evaluator.get_aggregate_metrics(results)

            # Log benchmark results
            logger.info(f"Quality Benchmark Results: {aggregate}")

            return {
                "benchmark_results": results,
                "aggregate_metrics": aggregate,
                "timestamp": datetime.utcnow().isoformat(),
            }

        background_tasks.add_task(run_benchmark)

        return {
            "status": "benchmark_started",
            "message": "Quality benchmark has been started in background",
            "test_cases": len(benchmark_cases),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
