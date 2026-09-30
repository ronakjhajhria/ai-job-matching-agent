from app.llm.provider import LLMProvider
from app.llm.schemas import RagResponse
from app.llm.prompts import rag_qa_messages
from app.rag.retriever import Retriever

class RAGAnswerGenerator:
    """Combines Retrieval and LLM Generation to answer questions."""
    
    def __init__(self, llm_provider: LLMProvider, retriever: Retriever):
        self.llm = llm_provider
        self.retriever = retriever

    def answer_question(self, query: str, top_k: int = 5) -> RagResponse:
        """
        End-to-end RAG pipeline: Retrieve -> Format -> Generate.
        """
        # 1. Retrieve relevant chunks
        chunks = self.retriever.retrieve(query, top_k=top_k)
        
        if not chunks:
            # Handle retrieval failure gracefully
            return RagResponse(
                answer="I could not find any relevant information in the uploaded documents to answer your question.",
                citations=[]
            )

        # 2. Format context for the LLM
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.metadata.get("source", "Unknown Source")
            context_parts.append(f"--- Document: {source} (Chunk {i}) ---\n{chunk.text}")
            
        formatted_context = "\n\n".join(context_parts)
        
        # 3. Generate structured answer with citations
        messages = rag_qa_messages(query=query, context=formatted_context)
        
        return self.llm.generate_structured(
            messages=messages,
            response_model=RagResponse
        )
