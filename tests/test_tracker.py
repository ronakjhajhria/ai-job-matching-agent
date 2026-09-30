"""Tests for Phase 11 — Application Tracker."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import create_app
from app.core.config import Settings


@pytest.fixture
def client():
    app = create_app(settings=Settings(environment="test", openai_api_key=None))
    return TestClient(app)


def test_update_and_list(client):
    # Update a job application
    payload = {
        "job_id": "job-001",
        "company": "TechCorp",
        "role": "Backend Engineer",
        "status": "applied",
        "date_updated": datetime.utcnow().isoformat(),
        "notes": "Referred by Alice"
    }
    r = client.post("/api/v1/tracker/update", json=payload)
    assert r.status_code == 200
    assert r.json()["job_id"] == "job-001"

    # List all
    r = client.get("/api/v1/tracker/list")
    assert r.status_code == 200
    assert len(r.json()) == 1

    # Filter by status
    r = client.get("/api/v1/tracker/list?status=applied")
    assert r.status_code == 200
    assert r.json()[0]["status"] == "applied"

    r = client.get("/api/v1/tracker/list?status=interview")
    assert r.status_code == 200
    assert len(r.json()) == 0
