import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.core.config import Settings
from app.llm.schemas import RagResponse, Citation
from app.documents.chunker import DocumentChunk
from app.rag.retriever import Retriever

class MockRetriever(Retriever):
    def __init__(self):
        pass

    def retrieve(self, query, top_k=5, metadata_filter=None):
        if "fail" in query.lower():
            return []
        return [
            DocumentChunk(text="Python and Docker are great.", metadata={"source": "resume.pdf"})
        ]

class MockRagGenerator:
    def answer_question(self, query, top_k=5):
        if "fail" in query.lower():
            return RagResponse(answer="I could not find any relevant information in the uploaded documents to answer your question.", citations=[])
            
        return RagResponse(
            answer="You know Python and Docker.",
            citations=[Citation(source_document="resume.pdf", exact_quote="Python and Docker")]
        )

@pytest.fixture
def rag_client():
    settings = Settings(service_name="TestRAG", environment="test", openai_api_key=None)
    mock_gen = MockRagGenerator()
    app = create_app(settings=settings, rag_generator=mock_gen)
    return TestClient(app)

def test_rag_ask(rag_client):
    payload = {"query": "What technologies do I know?"}
    response = rag_client.post("/api/v1/rag/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "You know Python and Docker."
    assert len(data["citations"]) == 1
    assert data["citations"][0]["source_document"] == "resume.pdf"

def test_rag_ask_no_results(rag_client):
    payload = {"query": "fail query"}
    response = rag_client.post("/api/v1/rag/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "could not find" in data["answer"].lower()
    assert len(data["citations"]) == 0
