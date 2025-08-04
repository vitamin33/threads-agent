"""
Test cases for Document Processor - handles chunking strategies and text processing.

Following TDD principles: Write the SIMPLEST test that could fail first.
"""

from services.rag_pipeline.processing.document_processor import DocumentProcessor


class TestDocumentProcessor:
    """Test Document Processor for different chunking strategies."""

    def test_chunk_text_returns_list_of_chunks(self):
        """
        FAILING TEST: Chunk text into smaller pieces.

        This is the SIMPLEST test - chunk text and get back a list.
        """
        # Arrange
        processor = DocumentProcessor()
        text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four."

        # Act
        chunks = processor.chunk_text(text, chunk_size=50)

        # Assert
        assert isinstance(chunks, list)
        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk) <= 50 for chunk in chunks)

    def test_semantic_chunking_preserves_sentence_boundaries(self):
        """
        FAILING TEST: Semantic chunking should not break sentences.

        This tests a more sophisticated chunking strategy.
        """
        # Arrange
        processor = DocumentProcessor()
        text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here."

        # Act
        chunks = processor.chunk_text_semantic(text, max_chunk_size=40)

        # Assert
        assert isinstance(chunks, list)
        assert len(chunks) > 1
        # Each chunk should end with a sentence boundary (period + space or end of text)
        for chunk in chunks[:-1]:  # All except last chunk
            assert chunk.rstrip().endswith(".")
        # This will FAIL - semantic chunking not implemented yet
