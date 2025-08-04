"""Document Processor for intelligent chunking and preprocessing."""

import re
import hashlib
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    MarkdownTextSplitter,
)


class ChunkingStrategy(Enum):
    """Chunking strategies for document processing."""

    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    SLIDING_WINDOW = "sliding_window"
    MARKDOWN = "markdown"


@dataclass
class DocumentChunk:
    """Represents a chunk of a document."""

    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    start_index: int
    end_index: int


class DocumentProcessor:
    """Processes documents into chunks for vector storage."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
        separators: Optional[List[str]] = None,
    ):
        """Initialize document processor.

        Args:
            chunk_size: Target size for chunks
            chunk_overlap: Overlap between chunks
            strategy: Chunking strategy to use
            separators: Custom separators for splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

        self._init_splitters()

    def _init_splitters(self):
        """Initialize text splitters based on strategy."""
        if self.strategy == ChunkingStrategy.RECURSIVE:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=self.separators,
                length_function=len,
            )
        elif self.strategy == ChunkingStrategy.MARKDOWN:
            self.splitter = MarkdownTextSplitter(
                chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
            )

    def process_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        preserve_structure: bool = False,
        enrich_metadata: bool = False,
        preserve_code_blocks: bool = False,
    ) -> List[DocumentChunk]:
        """Process text into chunks.

        Args:
            text: Text to process
            metadata: Base metadata for all chunks
            preserve_structure: Preserve document structure (headers, etc.)
            enrich_metadata: Add additional metadata (word count, etc.)
            preserve_code_blocks: Keep code blocks intact

        Returns:
            List of DocumentChunk objects
        """
        if not text or text.isspace():
            return []

        metadata = metadata or {}
        chunks = []

        # Handle different strategies
        if self.strategy == ChunkingStrategy.SEMANTIC:
            chunk_texts = self._semantic_chunk(text)
        elif self.strategy == ChunkingStrategy.SLIDING_WINDOW:
            chunk_texts = self._sliding_window_chunk(text)
        else:
            # Use the initialized splitter
            if preserve_code_blocks:
                text = self._protect_code_blocks(text)

            chunk_texts = self.splitter.split_text(text)

            if preserve_code_blocks:
                chunk_texts = [
                    self._restore_code_blocks(chunk) for chunk in chunk_texts
                ]

        # Create DocumentChunk objects
        current_index = 0
        for i, chunk_text in enumerate(chunk_texts):
            # Find chunk position in original text
            start_index = text.find(chunk_text, current_index)
            if start_index == -1:
                start_index = current_index
            end_index = start_index + len(chunk_text)
            current_index = end_index

            # Generate chunk ID
            doc_id = metadata.get("doc_id", "unknown")
            chunk_id = (
                f"{doc_id}_chunk_{i}_{hashlib.md5(chunk_text.encode()).hexdigest()[:8]}"
            )

            # Create chunk metadata
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunk_texts),
                "chunk_size": len(chunk_text),
                "strategy": self.strategy.value,
            }

            # Detect code blocks
            if preserve_code_blocks and "```" in chunk_text:
                chunk_metadata["has_code"] = True

            # Enrich metadata if requested
            if enrich_metadata:
                chunk_metadata.update(self._enrich_chunk_metadata(chunk_text))

            # Preserve structure information
            if preserve_structure:
                chunk_metadata.update(self._extract_structure_info(chunk_text))

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    content=chunk_text,
                    metadata=chunk_metadata,
                    start_index=start_index,
                    end_index=end_index,
                )
            )

        return chunks

    def _semantic_chunk(self, text: str) -> List[str]:
        """Perform semantic chunking based on sentence boundaries."""
        # Simple semantic chunking based on sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > self.chunk_size and current_chunk:
                # Create chunk
                chunks.append(" ".join(current_chunk))

                # Start new chunk with overlap
                overlap_sentences = []
                overlap_size = 0
                for s in reversed(current_chunk):
                    if overlap_size < self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += len(s) + 1
                    else:
                        break

                current_chunk = overlap_sentences + [sentence]
                current_size = (
                    sum(len(s) for s in current_chunk) + len(current_chunk) - 1
                )
            else:
                current_chunk.append(sentence)
                current_size += sentence_size + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _sliding_window_chunk(self, text: str) -> List[str]:
        """Perform sliding window chunking."""
        chunks = []
        text_length = len(text)

        start = 0
        while start < text_length:
            end = min(start + self.chunk_size, text_length)

            # Find a good breaking point
            if end < text_length:
                # Look for sentence boundary
                for sep in [". ", "! ", "? ", "\n", " "]:
                    break_point = text.rfind(sep, start, end)
                    if break_point > start:
                        end = break_point + len(sep)
                        break

            chunk = text[start:end]
            chunks.append(chunk)

            # Move window with overlap
            start = end - self.chunk_overlap

            # Prevent infinite loop
            if start >= text_length - 1:
                break

        return chunks

    def _protect_code_blocks(self, text: str) -> str:
        """Temporarily replace code blocks to prevent splitting."""
        self._code_blocks = []

        def replace_code(match):
            self._code_blocks.append(match.group(0))
            return f"__CODE_BLOCK_{len(self._code_blocks) - 1}__"

        # Replace code blocks with placeholders
        text = re.sub(r"```[\s\S]*?```", replace_code, text)
        return text

    def _restore_code_blocks(self, text: str) -> str:
        """Restore code blocks from placeholders."""

        def restore_code(match):
            index = int(match.group(1))
            return (
                self._code_blocks[index]
                if index < len(self._code_blocks)
                else match.group(0)
            )

        text = re.sub(r"__CODE_BLOCK_(\d+)__", restore_code, text)
        return text

    def _enrich_chunk_metadata(self, chunk_text: str) -> Dict[str, Any]:
        """Add enriched metadata to chunk."""
        words = chunk_text.split()

        return {
            "word_count": len(words),
            "char_count": len(chunk_text),
            "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
            "has_numbers": bool(re.search(r"\d", chunk_text)),
            "has_urls": bool(re.search(r"https?://\S+", chunk_text)),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _extract_structure_info(self, chunk_text: str) -> Dict[str, Any]:
        """Extract structural information from chunk."""
        info = {}

        # Check for headers
        header_match = re.search(r"^#+\s+(.+)$", chunk_text, re.MULTILINE)
        if header_match:
            info["has_header"] = True
            info["header_level"] = len(header_match.group(0).split()[0])

        # Check for lists
        if re.search(r"^\s*[-*+]\s+", chunk_text, re.MULTILINE):
            info["has_list"] = True

        # Check for numbered lists
        if re.search(r"^\s*\d+\.\s+", chunk_text, re.MULTILINE):
            info["has_numbered_list"] = True

        return info
