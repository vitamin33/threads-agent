"""
Retrieval Pipeline - handles search and re-ranking.

Following TDD: MINIMAL implementation to make the test pass.
"""

from typing import List, Dict, Any


class RetrievalPipeline:
    """
    Retrieval pipeline for RAG system.

    MINIMAL implementation - just enough to make the test pass.
    """

    def __init__(self):
        """Initialize the retrieval pipeline."""
        self.documents: List[Dict[str, Any]] = []

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the retrieval system."""
        self.documents = documents

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        MINIMAL: Simple keyword matching with basic scoring.
        """
        # Simple keyword-based scoring
        query_words = query.lower().split()

        # Score each document
        for doc in self.documents:
            text_words = doc["text"].lower().split()

            # Simple relevance score: count of matching words
            matches = sum(1 for word in query_words if word in text_words)
            doc["score"] = matches / len(query_words) if query_words else 0.0

        # Sort by score (descending) and limit to top_k
        sorted_docs = sorted(self.documents, key=lambda x: x["score"], reverse=True)

        # Only return documents with score > 0 (some relevance)
        relevant_docs = [doc for doc in sorted_docs if doc["score"] > 0]

        return relevant_docs[:top_k]
