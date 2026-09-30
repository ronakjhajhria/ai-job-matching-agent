from pydantic import BaseModel

class DocumentChunk(BaseModel):
    """Represents a chunk of text with its metadata."""
    text: str
    metadata: dict[str, str | int | float]

class TextChunker:
    """Splits large texts into overlapping chunks to fit within LLM context limits."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, base_metadata: dict[str, str | int | float] | None = None) -> list[DocumentChunk]:
        """
        Split text into overlapping chunks.
        
        This uses a simple character-based sliding window.
        A production system might use token-based chunking (e.g., tiktoken) 
        or semantic recursive chunking.
        """
        if not text:
            return []
            
        base_metadata = base_metadata or {}
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size
            
            # If we're not at the very end, try to find a nice breaking point (like a newline or space)
            # so we don't cut a word in half.
            if end < text_length:
                # Look for a newline or space within the last 50 characters of the chunk
                last_newline = text.rfind('\n', start, end)
                last_space = text.rfind(' ', start, end)
                
                if last_newline != -1 and last_newline > end - 100:
                    end = last_newline + 1
                elif last_space != -1 and last_space > end - 50:
                    end = last_space + 1

            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk_meta = base_metadata.copy()
                chunk_meta["char_start"] = start
                chunk_meta["char_end"] = end
                chunks.append(DocumentChunk(text=chunk_text, metadata=chunk_meta))
                
            # Move start forward, but step back by chunk_overlap
            start = end - self.chunk_overlap

        return chunks
