import pytest
import os
from pathlib import Path

from app.documents.parser import DocumentParser
from app.documents.chunker import TextChunker
from app.embeddings.provider import EmbeddingsProvider
from app.vectorstore.qdrant_store import QdrantStore
from app.rag.ingestion import IngestionPipeline

class MockEmbeddingsProvider(EmbeddingsProvider):
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # Return a dummy 3-dimensional vector for each text
        return [[0.1, 0.2, 0.3] for _ in texts]
        
    def embed_query(self, query: str) -> list[float]:
        return [0.1, 0.2, 0.3]

def test_text_chunking():
    chunker = TextChunker(chunk_size=10, chunk_overlap=2)
    # 26 chars long
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = chunker.chunk_text(text)
    
    # Expected sliding window:
    # chunk 1: 0 to 10 -> "abcdefghij" (overlap next at index 8)
    # chunk 2: 8 to 18 -> "ijklmnopqr" (overlap next at index 16)
    # chunk 3: 16 to 26 -> "qrstuvwxyz"
    assert len(chunks) == 3
    assert chunks[0].text == "abcdefghij"
    assert chunks[1].text == "ijklmnopqr"
    assert chunks[2].text == "qrstuvwxyz"

def test_clean_text():
    dirty_text = "This   is \n\n\n a messy \t text."
    clean = DocumentParser.clean_text(dirty_text)
    assert clean == "This is \n\n a messy text."

def test_ingestion_pipeline(tmp_path):
    # 1. Create a dummy text file
    dummy_file = tmp_path / "resume.txt"
    dummy_file.write_text("Hello world! This is my resume.\n" * 50) # make it long enough to chunk
    
    # 2. Setup mock pipeline
    embeddings = MockEmbeddingsProvider()
    store = QdrantStore(collection_name="test_col", embeddings=embeddings, vector_size=3)
    pipeline = IngestionPipeline(vector_store=store, chunk_size=100, chunk_overlap=20)
    
    # 3. Run ingestion
    num_chunks = pipeline.ingest_file(dummy_file)
    
    # 4. Verify
    assert num_chunks > 0
    # Verify qdrant has points
    count = store.client.count(collection_name="test_col")
    assert count.count == num_chunks
