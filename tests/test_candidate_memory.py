import fakeredis
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.db.session import create_session_factory
from app.main import create_app
from app.memory.preferences import SearchPreferences, SqlCandidatePreferencesRepository
from app.memory.session_store import RedisConversationStore


@pytest.fixture
def preference_repository():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    repository = SqlCandidatePreferencesRepository(create_session_factory(engine))
    yield repository
    engine.dispose()


@pytest.fixture
def client(preference_repository):
    redis_client = fakeredis.FakeRedis(decode_responses=True)
    session_store = RedisConversationStore(redis_client, ttl_seconds=120, max_messages=4)
    app = create_app(
        settings=Settings(environment="test", openai_api_key=None),
        candidate_preferences=preference_repository,
        conversation_store=session_store,
    )
    with TestClient(app) as test_client:
        yield test_client


def test_preferences_survive_repository_reuse(preference_repository):
    preferences = SearchPreferences(
        preferred_roles=["Backend Engineer"],
        skills=["Python", "PostgreSQL"],
        locations=["Remote"],
        min_salary=100000,
    )

    saved = preference_repository.save("candidate-1", preferences)
    loaded = preference_repository.get("candidate-1")

    assert saved.candidate_id == "candidate-1"
    assert loaded is not None
    assert loaded.preferences == preferences
    assert loaded.updated_at is not None


def test_preferences_api_upserts_and_reads(client):
    response = client.put(
        "/api/v1/preferences/candidate-2",
        json={"preferred_roles": ["ML Engineer"], "skills": ["Python"]},
    )

    assert response.status_code == 200
    assert response.json()["preferences"]["preferred_roles"] == ["ML Engineer"]

    loaded = client.get("/api/v1/preferences/candidate-2")
    assert loaded.status_code == 200
    assert loaded.json()["preferences"]["skills"] == ["Python"]


def test_missing_preferences_return_404(client):
    response = client.get("/api/v1/preferences/unknown")

    assert response.status_code == 404


def test_invalid_salary_range_is_rejected():
    with pytest.raises(ValidationError):
        SearchPreferences(min_salary=150000, max_salary=100000)


def test_session_api_keeps_only_recent_messages_and_refreshes_ttl(client):
    for number in range(5):
        response = client.post(
            "/api/v1/sessions/session-1/messages",
            json={"role": "user", "content": f"message {number}"},
        )
        assert response.status_code == 200

    messages = client.get("/api/v1/sessions/session-1/messages").json()

    assert [message["content"] for message in messages] == [
        "message 1",
        "message 2",
        "message 3",
        "message 4",
    ]