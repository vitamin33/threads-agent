"""
Embedding Service - handles text-to-vector conversion with caching.

Following TDD: MINIMAL implementation to make the test pass.
"""

import numpy as np
import hashlib
from typing import Dict


class EmbeddingService:
    """
    Embedding service for RAG pipeline.

    MINIMAL implementation - just enough to make the test pass.
    """

    def __init__(self, use_cache: bool = False):
        """Initialize with optional caching."""
        self.use_cache = use_cache
        self._cache: Dict[str, np.ndarray] = {}
        self._cache_stats = {"hits": 0, "misses": 0}

    def embed_text(self, text: str) -> np.ndarray:
        """
        Convert text to embedding vector.

        MINIMAL: Generate a deterministic fake embedding based on text hash.
        In production, this would use OpenAI embeddings or similar.
        """
        # Check cache first if enabled
        if self.use_cache and text in self._cache:
            self._cache_stats["hits"] += 1
            return self._cache[text]

        # Cache miss or caching disabled
        if self.use_cache:
            self._cache_stats["misses"] += 1

        # Create a deterministic "embedding" based on text hash
        # This ensures same text always produces same embedding
        text_hash = hashlib.md5(text.encode()).hexdigest()

        # Convert hex chars to numbers and create a 384-dim vector (common size)
        embedding_values = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i : i + 2]
            value = int(hex_pair, 16) / 255.0  # Normalize to [0,1]
            embedding_values.append(value)

        # Pad or truncate to make it 384 dimensions
        while len(embedding_values) < 384:
            embedding_values.extend(embedding_values[: 384 - len(embedding_values)])

        embedding = np.array(embedding_values[:384], dtype=np.float32)

        # Store in cache if enabled
        if self.use_cache:
            self._cache[text] = embedding

        return embedding

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return self._cache_stats.copy()
