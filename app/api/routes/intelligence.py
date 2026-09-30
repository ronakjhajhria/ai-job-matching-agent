"""Phase 5 & 6 API: Resume & Job Description parsing endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.llm.provider import LLMProvider, LLMProviderError
from app.llm.schemas_intelligence import ResumeProfile, JobDescription
from app.matching.analyzer import CareerAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/intelligence", tags=["Intelligence"])


class TextRequest(BaseModel):
    text: str = Field(min_length=10, max_length=20000)


def _get_analyzer(request: Request) -> CareerAnalyzer:
    provider: LLMProvider | None = request.app.state.llm_provider
    if not provider:
        raise HTTPException(503, "LLM provider is not configured.")
    return CareerAnalyzer(llm=provider)


@router.post("/parse/resume", response_model=ResumeProfile)
def parse_resume(payload: TextRequest, request: Request) -> ResumeProfile:
    """Parse a resume text into a structured profile."""
    try:
        return _get_analyzer(request).parse_resume(payload.text)
    except LLMProviderError as e:
        logger.error(f"Resume parsing failed: {e}")
        raise HTTPException(502, "LLM provider request failed.")


@router.post("/parse/job", response_model=JobDescription)
def parse_job(payload: TextRequest, request: Request) -> JobDescription:
    """Parse a job description text into a structured profile."""
    try:
        return _get_analyzer(request).parse_job(payload.text)
    except LLMProviderError as e:
        logger.error(f"Job parsing failed: {e}")
        raise HTTPException(502, "LLM provider request failed.")
