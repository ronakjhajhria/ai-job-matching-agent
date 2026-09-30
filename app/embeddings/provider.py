from typing import Protocol

class EmbeddingsProvider(Protocol):
    """Protocol for generating vector embeddings from text."""
    
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Convert a list of strings into a list of vector embeddings.
        
        Args:
            texts: List of text strings to embed.
            
        Returns:
            List of float arrays representing the semantic vectors.
        """
        ...
        
    def embed_query(self, query: str) -> list[float]:
        """Convert a single search query string into a vector."""
        ...
