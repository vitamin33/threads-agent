"""Embedding Service for generating and caching embeddings."""

import asyncio
import hashlib
import json
import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

from openai import OpenAI
import tiktoken
from redis.asyncio import Redis as AsyncRedis

logger = logging.getLogger(__name__)


class EmbeddingModel(Enum):
    """Supported embedding models."""

    ADA_002 = "text-embedding-ada-002"
    SMALL_3 = "text-embedding-3-small"
    LARGE_3 = "text-embedding-3-large"

    @property
    def dimension(self) -> int:
        """Get embedding dimension for model."""
        dimensions = {self.ADA_002: 1536, self.SMALL_3: 1536, self.LARGE_3: 3072}
        return dimensions.get(self, 1536)


class EmbeddingCache:
    """Redis-based cache for embeddings with connection pooling."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ttl: int = 86400,  # 24 hours
        prefix: str = "emb",
        max_connections: int = 20,
        retry_on_timeout: bool = True,
        socket_keepalive: bool = True,
    ):
        """Initialize embedding cache with optimized connection pool.

        Args:
            redis_url: Redis connection URL
            ttl: Time to live in seconds
            prefix: Key prefix for cache entries
            max_connections: Maximum connections in pool
            retry_on_timeout: Retry on timeout errors
            socket_keepalive: Enable socket keepalive
        """
        self.redis_url = redis_url
        self.ttl = ttl
        self.prefix = prefix
        self.max_connections = max_connections
        self.retry_on_timeout = retry_on_timeout
        self.socket_keepalive = socket_keepalive
        self._redis_pool = None

    async def _get_redis(self) -> AsyncRedis:
        """Get or create Redis connection pool."""
        if self._redis_pool is None:
            self._redis_pool = await AsyncRedis.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                retry_on_timeout=self.retry_on_timeout,
                socket_keepalive=self.socket_keepalive,
                socket_keepalive_options={
                    "TCP_KEEPIDLE": 1,
                    "TCP_KEEPINTVL": 3,
                    "TCP_KEEPCNT": 5,
                },
                health_check_interval=30,
            )
        return self._redis_pool

    def _generate_key(self, text: str) -> str:
        """Generate cache key for text."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"{self.prefix}:{text_hash}"

    async def get(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache."""
        try:
            redis = await self._get_redis()
            key = self._generate_key(text)
            data = await redis.get(key)

            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def set(self, text: str, embedding: List[float]):
        """Store embedding in cache."""
        try:
            redis = await self._get_redis()
            key = self._generate_key(text)
            data = json.dumps(embedding)
            await redis.setex(key, self.ttl, data)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    async def get_batch(self, texts: List[str]) -> Dict[str, List[float]]:
        """Get multiple embeddings from cache with pipeline optimization."""
        try:
            redis = await self._get_redis()
            keys = [self._generate_key(text) for text in texts]

            # Use Redis pipeline for batch operations
            async with redis.pipeline(transaction=False) as pipe:
                for key in keys:
                    pipe.get(key)
                values = await pipe.execute()

            results = {}
            for text, value in zip(texts, values):
                if value:
                    try:
                        results[text] = json.loads(value)
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Failed to decode cached embedding for {text[:50]}: {e}"
                        )
            return results
        except Exception as e:
            logger.warning(f"Cache batch get error: {e}")
            return {}

    async def set_batch(self, text_embedding_pairs: List[tuple]):
        """Set multiple embeddings in cache efficiently."""
        try:
            redis = await self._get_redis()

            # Use Redis pipeline for batch operations
            async with redis.pipeline(transaction=False) as pipe:
                for text, embedding in text_embedding_pairs:
                    key = self._generate_key(text)
                    data = json.dumps(embedding)
                    pipe.setex(key, self.ttl, data)
                await pipe.execute()
        except Exception as e:
            logger.warning(f"Cache batch set error: {e}")


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(
        self,
        model: EmbeddingModel = EmbeddingModel.ADA_002,
        api_key: Optional[str] = None,
        cache: Optional[EmbeddingCache] = None,
        max_retries: int = 3,
        batch_size: int = 100,
    ):
        """Initialize embedding service.

        Args:
            model: Embedding model to use
            api_key: OpenAI API key
            cache: Optional embedding cache
            max_retries: Maximum retry attempts
            batch_size: Maximum batch size for API calls
        """
        self.model = model
        self.dimension = model.dimension
        self.client = OpenAI(api_key=api_key)
        self.cache = cache or EmbeddingCache()
        self.max_retries = max_retries
        self.batch_size = batch_size

        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model(model.value)
        except Exception:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    async def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """Generate embedding for single text.

        Args:
            text: Text to embed
            use_cache: Whether to use cache

        Returns:
            Embedding vector
        """
        # Check cache first
        if use_cache and self.cache:
            cached = await self.cache.get(text)
            if cached:
                logger.debug(f"Cache hit for text: {text[:50]}...")
                return cached

        # Generate embedding
        embedding = await self._generate_embedding([text])
        embedding = embedding[0]

        # Store in cache
        if use_cache and self.cache:
            await self.cache.set(text, embedding)

        return embedding

    async def embed_batch(
        self, texts: List[str], use_cache: bool = True
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            use_cache: Whether to use cache

        Returns:
            List of embedding vectors
        """
        embeddings = [None] * len(texts)
        uncached_texts = []
        uncached_indices = []

        # Check cache for all texts
        if use_cache and self.cache:
            cached_embeddings = await self.cache.get_batch(texts)

            for i, text in enumerate(texts):
                if text in cached_embeddings:
                    embeddings[i] = cached_embeddings[text]
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
        else:
            uncached_texts = texts
            uncached_indices = list(range(len(texts)))

        # Generate embeddings for uncached texts with optimized batching
        if uncached_texts:
            all_new_embeddings = []
            # Process in batches with concurrent API calls
            batch_tasks = []

            for batch_start in range(0, len(uncached_texts), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(uncached_texts))
                batch_texts = uncached_texts[batch_start:batch_end]
                batch_tasks.append(self._generate_embedding(batch_texts))

            # Execute all batches concurrently (up to reasonable limit)
            max_concurrent = min(3, len(batch_tasks))  # Limit concurrent API calls
            for i in range(0, len(batch_tasks), max_concurrent):
                concurrent_batch = batch_tasks[i : i + max_concurrent]
                batch_results = await asyncio.gather(
                    *concurrent_batch, return_exceptions=True
                )

                for batch_result in batch_results:
                    if isinstance(batch_result, Exception):
                        logger.error(f"Batch embedding failed: {batch_result}")
                        continue
                    all_new_embeddings.extend(batch_result)

            # Store results and cache in batch
            cache_pairs = []
            for i, (text, embedding) in enumerate(
                zip(uncached_texts, all_new_embeddings)
            ):
                original_index = uncached_indices[i]
                embeddings[original_index] = embedding

                if use_cache and self.cache:
                    cache_pairs.append((text, embedding))

            # Batch cache all new embeddings
            if cache_pairs and use_cache and self.cache:
                await self.cache.set_batch(cache_pairs)

        return embeddings

    async def _generate_embedding(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API with retry logic."""
        for attempt in range(self.max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.model.value, input=texts
                )
                return [data.embedding for data in response.data]

            except Exception as e:
                if "rate_limit" in str(e).lower() and attempt < self.max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Embedding generation failed: {e}")
                    raise

    async def embed_with_metadata(
        self, text: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate embedding with metadata.

        Args:
            text: Text to embed
            metadata: Associated metadata

        Returns:
            Dict with embedding, metadata, and stats
        """
        embedding = await self.embed_text(text)
        token_count = self.estimate_tokens(text)

        return {
            "embedding": embedding,
            "metadata": metadata,
            "token_count": token_count,
            "model": self.model.value,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Embed document chunks efficiently.

        Args:
            chunks: List of chunks with content and metadata

        Returns:
            List of results with embeddings and metadata
        """
        texts = [chunk["content"] for chunk in chunks]
        embeddings = await self.embed_batch(texts)

        results = []
        for chunk, embedding in zip(chunks, embeddings):
            results.append(
                {
                    "embedding": embedding,
                    "metadata": chunk.get("metadata", {}),
                    "content": chunk["content"],
                }
            )

        return results

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        try:
            return len(self.tokenizer.encode(text))
        except Exception:
            # Fallback estimation: ~4 characters per token
            return len(text) // 4
