"""Phase 7 API: Semantic Job Matching endpoint."""

import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.llm.provider import LLMProvider, LLMProviderError
from app.llm.schemas_intelligence import ResumeProfile, JobDescription, JobMatchResult
from app.matching.analyzer import CareerAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/matching", tags=["Matching"])


class MatchRequest(BaseModel):
    resume_text: str
    job_description_text: str


@router.post("/analyze", response_model=JobMatchResult)
def analyze_match(payload: MatchRequest, request: Request) -> JobMatchResult:
    """
    Parse a resume and job description then produce a semantic match report.
    Returns matching skills, gaps, evidence, and a 1–10 score.
    """
    provider: LLMProvider | None = request.app.state.llm_provider
    if not provider:
        raise HTTPException(503, "LLM provider is not configured.")

    try:
        analyzer = CareerAnalyzer(llm=provider)
        resume = analyzer.parse_resume(payload.resume_text)
        job = analyzer.parse_job(payload.job_description_text)
        return analyzer.match_profiles(resume, job)
    except LLMProviderError as e:
        logger.error(f"Matching analysis failed: {e}")
        raise HTTPException(502, "LLM provider request failed.")
