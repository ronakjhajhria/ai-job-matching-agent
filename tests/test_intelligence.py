"""Tests for Phase 5/6/7 — Intelligence & Matching."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.core.config import Settings
from app.llm.provider import LLMProvider
from app.llm.schemas_intelligence import ResumeProfile, JobDescription, JobMatchResult


class MockLLMForIntelligence(LLMProvider):
    def generate_structured(self, messages, response_model):
        if response_model == ResumeProfile:
            return ResumeProfile(
                name="Jane Doe",
                education=["B.S. Computer Science, MIT"],
                skills=["Python", "FastAPI"],
                projects=["JobMind"],
                experience=["Backend Engineer at TechCorp"],
                achievements=["Scaled API to 1M requests/day"],
                preferred_roles=["Backend Engineer"]
            )
        if response_model == JobDescription:
            return JobDescription(
                job_id="test-1",
                role="Backend Engineer",
                company="Acme",
                required_skills=["Python"],
                preferred_skills=["Docker"],
                responsibilities=["Build APIs"],
                experience_requirements="2+ years",
                education_requirements="None",
                location="Remote",
                technologies=["Python"]
            )
        if response_model == JobMatchResult:
            return JobMatchResult(
                match_score_1_to_10=9,
                matching_skills=["Python"],
                missing_skills=[],
                related_skills=["FastAPI"],
                evidence_from_resume=["Backend Engineer at TechCorp"],
                evidence_from_jd=["Build APIs"],
                explanation="Strong match."
            )
        raise ValueError(f"Unexpected model: {response_model}")


@pytest.fixture
def client():
    app = create_app(
        settings=Settings(environment="test", openai_api_key=None),
        llm_provider=MockLLMForIntelligence()
    )
    return TestClient(app)


def test_parse_resume(client):
    r = client.post("/api/v1/intelligence/parse/resume", json={"text": "I am Jane, a Python developer."})
    assert r.status_code == 200
    assert r.json()["name"] == "Jane Doe"
    assert "Python" in r.json()["skills"]


def test_parse_job(client):
    r = client.post("/api/v1/intelligence/parse/job", json={"text": "Looking for a Python Backend Engineer."})
    assert r.status_code == 200
    assert r.json()["role"] == "Backend Engineer"


def test_match_analyze(client):
    r = client.post("/api/v1/matching/analyze", json={
        "resume_text": "Python developer.",
        "job_description_text": "Looking for a Python engineer."
    })
    assert r.status_code == 200
    data = r.json()
    assert data["match_score_1_to_10"] == 9
    assert "Python" in data["matching_skills"]
