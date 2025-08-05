"""
Test cases for Embedding Service - handles text-to-vector conversion with caching.

Following TDD principles: Write the SIMPLEST test that could fail first.
"""

import numpy as np

from services.rag_pipeline.core.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Test Embedding Service for text-to-vector conversion."""

    def test_embed_text_returns_vector(self):
        """
        FAILING TEST: Convert text to embedding vector.

        This is the SIMPLEST test - embed text and get back a vector.
        """
        # Arrange
        service = EmbeddingService()
        text = "This is a test document."

        # Act
        embedding = service.embed_text(text)

        # Assert
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape[0] > 0  # Should have some dimensions
        assert len(embedding.shape) == 1  # Should be 1D vector

    def test_embed_text_caching_returns_same_vector(self):
        """
        FAILING TEST: Same text should return identical cached embeddings.

        This tests the caching functionality for performance.
        """
        # Arrange
        service = EmbeddingService(use_cache=True)
        text = "This is a test document for caching."

        # Act
        embedding1 = service.embed_text(text)
        embedding2 = service.embed_text(text)  # Should hit cache

        # Assert
        assert np.array_equal(embedding1, embedding2)
        assert service.get_cache_stats()["hits"] == 1
        assert service.get_cache_stats()["misses"] == 1
        # This will FAIL - caching not implemented yet
