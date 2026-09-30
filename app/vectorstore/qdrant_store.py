import uuid
from typing import Any
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.documents.chunker import DocumentChunk
from app.embeddings.provider import EmbeddingsProvider

class QdrantStore:
    """Wrapper around Qdrant Vector Database."""
    
    def __init__(self, collection_name: str, embeddings: EmbeddingsProvider, vector_size: int = 1536):
        # Using memory storage for simplicity right now. 
        # In production, this would point to a URL/host.
        self.client = QdrantClient(":memory:")
        self.collection_name = collection_name
        self.embeddings = embeddings
        self.vector_size = vector_size
        
        self._ensure_collection()

    def _ensure_collection(self):
        """Create the collection if it doesn't exist."""
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Embed text chunks and store them in Qdrant with metadata."""
        if not chunks:
            return

        texts = [chunk.text for chunk in chunks]
        vectors = self.embeddings.embed_texts(texts)
        
        points = []
        for chunk, vector in zip(chunks, vectors):
            point_id = str(uuid.uuid4())
            # We store the original text in the payload (metadata) so we can retrieve it
            payload = chunk.metadata.copy()
            payload["text"] = chunk.text
            
            points.append(models.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            ))
            
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def search(self, query_vector: list[float], top_k: int = 5, metadata_filter: dict[str, Any] | None = None) -> list[DocumentChunk]:
        """
        Search the vector database for the most similar chunks.
        
        Args:
            query_vector: The embedded query vector.
            top_k: Number of results to return.
            metadata_filter: Optional exact-match filters (e.g. {"source": "resume.pdf"})
            
        Returns:
            List of DocumentChunks ranked by cosine similarity.
        """
        # Build Qdrant filter if provided
        query_filter = None
        if metadata_filter:
            must_conditions = [
                models.FieldCondition(key=k, match=models.MatchValue(value=v))
                for k, v in metadata_filter.items()
            ]
            query_filter = models.Filter(must=must_conditions)
            
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter
        )
        
        # Reconstruct DocumentChunks from the payload
        chunks = []
        for result in search_results:
            payload = result.payload or {}
            text = payload.pop("text", "")
            chunks.append(DocumentChunk(text=text, metadata=payload))
            
        return chunks
