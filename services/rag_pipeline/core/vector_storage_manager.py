"""
Vector Storage Manager - Core RAG component extending Qdrant integration.

Following TDD: MINIMAL implementation to make the test pass.
"""

import uuid
from typing import Dict, Any, Union, List, Optional


class VectorStorageManager:
    """
    Vector Storage Manager for RAG pipeline.

    MINIMAL implementation - just enough to make the test pass.
    """

    def __init__(self, qdrant_collection: Optional[str] = None):
        """Initialize with optional Qdrant collection name."""
        self.qdrant_collection = qdrant_collection

    def store_document(
        self, document: str, metadata: Dict[str, Any]
    ) -> Dict[str, Union[str, int, List[str]]]:
        """
        Store a document and return a document ID.

        MINIMAL: Add chunking logic - if doc > 1000 chars, split it.
        """
        document_id = str(uuid.uuid4())

        # Simple chunking logic - if document is long, split it
        if len(document) > 1000:
            # Simple chunking: split by chunks of 500 characters
            chunk_size = 500
            chunks = [
                document[i : i + chunk_size]
                for i in range(0, len(document), chunk_size)
            ]
            chunks_created = len(chunks)
        else:
            chunks_created = 1

        # MINIMAL: Generate mock vector IDs for now
        # In real implementation, these would be Qdrant point IDs
        vector_ids = [f"{document_id}_chunk_{i}" for i in range(chunks_created)]

        result = {"document_id": document_id, "chunks_created": chunks_created}

        # Only add vector_ids if we have a Qdrant collection (integration test)
        if self.qdrant_collection:
            result["vector_ids"] = vector_ids

        return result
