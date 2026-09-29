import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app


def test_health_endpoint_returns_service_status() -> None:
    client = TestClient(create_app(Settings(service_name="Test JobMind")))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Test JobMind"}


def test_settings_read_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JOBMIND_SERVICE_NAME", "Configured JobMind")
    monkeypatch.setenv("JOBMIND_ENVIRONMENT", "test")

    settings = Settings()

    assert settings.service_name == "Configured JobMind"
    assert settings.environment == "test"


def test_settings_reject_unknown_log_level() -> None:
    with pytest.raises(ValidationError):
        Settings(log_level="TRACE")