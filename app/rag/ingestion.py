from pathlib import Path

from app.documents.parser import DocumentParser
from app.documents.chunker import TextChunker
from app.vectorstore.qdrant_store import QdrantStore

class IngestionPipeline:
    """Orchestrates the process of ingesting a document into the vector database."""
    
    def __init__(
        self, 
        vector_store: QdrantStore, 
        chunk_size: int = 1000, 
        chunk_overlap: int = 200
    ):
        self.vector_store = vector_store
        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
    def ingest_file(self, file_path: str | Path, source_name: str | None = None) -> int:
        """
        Process a file and store its chunks in the vector database.
        
        Args:
            file_path: Path to the PDF, TXT, or MD file.
            source_name: Optional logical name (defaults to file name).
            
        Returns:
            The number of chunks ingested.
        """
        path = Path(file_path)
        
        # 1. Text Extraction
        raw_text = DocumentParser.extract_text(path)
        
        # 2. Metadata Assignment
        metadata = {
            "source": source_name or path.name,
            "extension": path.suffix.lower()
        }
        
        # 3. Chunking (cleaning is handled implicitly by the Parser)
        chunks = self.chunker.chunk_text(raw_text, base_metadata=metadata)
        
        # 4. Embeddings & Storage
        self.vector_store.add_chunks(chunks)
        
        return len(chunks)
