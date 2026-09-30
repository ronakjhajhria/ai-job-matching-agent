import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.llm.prompts import skill_extraction_messages
from app.llm.provider import LLMProvider, LLMProviderError
from app.llm.schemas import SkillExtraction

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/skills", tags=["Skills"])

class SkillExtractionRequest(BaseModel):
    text: str = Field(min_length=10, max_length=20000)

@router.post("/extract", response_model=SkillExtraction)
def extract_skills(payload: SkillExtractionRequest, request: Request) -> SkillExtraction:
    """
    Extract explicitly supported skills from a resume or job description 
    using the configured LLM provider.
    """
    provider: LLMProvider | None = request.app.state.llm_provider
    if not provider:
        raise HTTPException(
            status_code=503,
            detail="LLM provider is not configured. Missing API key."
        )

    try:
        messages = skill_extraction_messages(payload.text)
        return provider.generate_structured(
            messages=messages,
            response_model=SkillExtraction,
        )
    except LLMProviderError as e:
        logger.error(f"Skill extraction failed: {e}")
        # Return generic 502 to avoid leaking internal API details
        raise HTTPException(
            status_code=502,
            detail="Upstream LLM provider request failed."
        ) from e
