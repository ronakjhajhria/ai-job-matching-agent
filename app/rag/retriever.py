from typing import Any

from app.documents.chunker import DocumentChunk
from app.embeddings.provider import EmbeddingsProvider
from app.vectorstore.qdrant_store import QdrantStore

class Retriever:
    """Handles the query embedding and vector search process."""
    
    def __init__(self, vector_store: QdrantStore, embeddings: EmbeddingsProvider):
        self.vector_store = vector_store
        self.embeddings = embeddings

    def retrieve(self, query: str, top_k: int = 5, metadata_filter: dict[str, Any] | None = None) -> list[DocumentChunk]:
        """
        Embed a user query and retrieve the most relevant document chunks.
        
        Args:
            query: The user's question.
            top_k: Number of relevant chunks to return.
            metadata_filter: Optional filter to restrict search (e.g. to a specific resume).
            
        Returns:
            A list of the most semantically similar DocumentChunks.
        """
        query_vector = self.embeddings.embed_query(query)
        return self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            metadata_filter=metadata_filter
        )
