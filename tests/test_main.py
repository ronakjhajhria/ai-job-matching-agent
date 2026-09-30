from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import Settings

def test_health_endpoint():
    """Test that the health endpoint returns the correct status and configuration."""
    # Use explicit settings for tests so they don't depend on local env vars
    test_settings = Settings(
        service_name="JobMindTest",
        environment="test",
        log_level="DEBUG"
    )
    
    app = create_app(test_settings)
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "JobMindTest"
    assert data["environment"] == "test"
