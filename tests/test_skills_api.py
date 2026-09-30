import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.core.config import Settings
from app.llm.provider import LLMProvider
from app.llm.schemas import SkillExtraction

class MockLLMProvider(LLMProvider):
    """A deterministic mock provider for testing without network calls."""
    def generate_structured(self, messages, response_model):
        return SkillExtraction(
            skills=["Python", "FastAPI"],
            summary="Backend API development"
        )

@pytest.fixture
def test_client():
    settings = Settings(
        service_name="JobMindTest",
        environment="test",
        # We don't need a real API key since we inject the mock provider
        openai_api_key=None 
    )
    mock_provider = MockLLMProvider()
    app = create_app(settings=settings, llm_provider=mock_provider)
    return TestClient(app)

def test_extract_skills(test_client):
    payload = {"text": "I am a backend developer using Python and FastAPI."}
    response = test_client.post("/api/v1/skills/extract", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["skills"] == ["Python", "FastAPI"]
    assert data["summary"] == "Backend API development"

def test_extract_skills_no_provider():
    """Test behavior when API key is missing (provider is None)."""
    settings = Settings(openai_api_key=None)
    app = create_app(settings=settings, llm_provider=None)
    client = TestClient(app)
    
    payload = {"text": "I am a backend developer using Python and FastAPI."}
    response = client.post("/api/v1/skills/extract", json=payload)
    
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]
