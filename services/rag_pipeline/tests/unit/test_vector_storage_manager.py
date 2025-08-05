"""
Test cases for Vector Storage Manager - the core RAG component.

Following TDD principles: Write the SIMPLEST test that could fail first.
"""

from services.rag_pipeline.core.vector_storage_manager import VectorStorageManager


class TestVectorStorageManager:
    """Test Vector Storage Manager - extends existing Qdrant integration."""

    def test_store_document_returns_document_id(self):
        """
        FAILING TEST: Store a document and get back a document ID.

        This is the SIMPLEST test - just store and get an ID back.
        We'll add complexity (chunking, embedding) in subsequent tests.
        """
        # Arrange
        manager = VectorStorageManager()
        document = "This is a test document for RAG pipeline."
        metadata = {"source": "test", "type": "text"}

        # Act
        result = manager.store_document(document, metadata)

        # Assert
        assert "document_id" in result
        assert isinstance(result["document_id"], str)
        assert len(result["document_id"]) > 0

    def test_store_long_document_returns_multiple_chunks(self):
        """
        FAILING TEST: Long documents should be chunked and return chunk info.

        This tests the document processing pipeline - chunking strategy.
        """
        # Arrange
        manager = VectorStorageManager()
        # Create a document that's definitely long enough to chunk (>1000 chars)
        long_document = "This is a test sentence. " * 50  # ~1250 characters
        metadata = {"source": "test", "type": "long_text"}

        # Act
        result = manager.store_document(long_document, metadata)

        # Assert
        assert "document_id" in result
        assert "chunks_created" in result
        assert isinstance(result["chunks_created"], int)
        assert result["chunks_created"] > 1  # Should be chunked

    def test_store_document_with_qdrant_integration(self):
        """
        FAILING TEST: Should integrate with existing Qdrant client.

        This tests the actual vector storage using the existing orchestrator integration.
        """
        # Arrange
        manager = VectorStorageManager(qdrant_collection="test_rag")
        document = "This is a test document for vector storage."
        metadata = {"source": "test", "type": "integration_test"}

        # Act
        result = manager.store_document(document, metadata)

        # Assert
        assert "document_id" in result
        assert "vector_ids" in result  # Should store vectors in Qdrant
        assert isinstance(result["vector_ids"], list)
        assert len(result["vector_ids"]) > 0
        # This will FAIL - Qdrant integration not implemented yet
