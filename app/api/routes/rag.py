import logging
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field

from app.llm.provider import LLMProvider, LLMProviderError
from app.llm.schemas import RagResponse
from app.rag.generator import RAGAnswerGenerator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])

class RagQueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=10)

def get_rag_generator(request: Request) -> RAGAnswerGenerator:
    """Dependency to retrieve the initialized RAG generator from app state."""
    generator = getattr(request.app.state, "rag_generator", None)
    if not generator:
        raise HTTPException(
            status_code=503,
            detail="RAG subsystem is not initialized."
        )
    return generator

@router.post("/ask", response_model=RagResponse)
def ask_question(
    payload: RagQueryRequest, 
    generator: RAGAnswerGenerator = Depends(get_rag_generator)
) -> RagResponse:
    """
    Ask a question against the ingested documents.
    Retrieves the most relevant chunks and generates an answer with citations.
    """
    try:
        return generator.answer_question(query=payload.query, top_k=payload.top_k)
    except LLMProviderError as e:
        logger.error(f"RAG generation failed: {e}")
        raise HTTPException(
            status_code=502,
            detail="Upstream LLM provider request failed during RAG."
        ) from e
