import openai
from app.embeddings.provider import EmbeddingsProvider

class OpenAIEmbeddingsProvider(EmbeddingsProvider):
    """OpenAI implementation for generating embeddings."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
            
        # OpenAI SDK natively supports batching texts in a single request
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        
        # Results might not be ordered identically to input depending on batching,
        # but OpenAI returns them sorted by the `index` property
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]
