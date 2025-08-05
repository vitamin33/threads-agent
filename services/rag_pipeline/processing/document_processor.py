"""
Document Processor - handles chunking strategies and text processing.

Following TDD: MINIMAL implementation to make the test pass.
"""

from typing import List


class DocumentProcessor:
    """
    Document processor for RAG pipeline.

    MINIMAL implementation - just enough to make the test pass.
    """

    def chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """
        Chunk text into smaller pieces.

        MINIMAL: Simple character-based chunking.
        """
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size]
            chunks.append(chunk)

        return chunks

    def chunk_text_semantic(self, text: str, max_chunk_size: int) -> List[str]:
        """
        Chunk text while preserving sentence boundaries.

        MINIMAL: Split by sentences, then group them into chunks.
        """
        # Split by sentence endings
        sentences = [s.strip() + "." for s in text.split(".") if s.strip()]

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # If adding this sentence would exceed max size, start a new chunk
            if (
                current_chunk
                and len(current_chunk) + len(sentence) + 1 > max_chunk_size
            ):
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
