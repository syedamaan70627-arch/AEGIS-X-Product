"""
Tests for AEGIS-X API Health & Status Endpoints.
"""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test public root GET / endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AEGIS-X API"
    assert data["status"] == "online"
    assert data["version"] == "0.1.0"
    assert data["health"] == "/health"
    assert data["readiness"] == "/ready"
    assert data["docs"] == "/docs"


def test_health_endpoint():
    """Test unversioned /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "AEGIS-X"
    assert data["api_version"] == "0.1.0"
    assert data["engine_available"] is True


def test_system_status_endpoint():
    """Test /api/v1/status capability discovery endpoint."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["api_status"] == "operational"
    assert ".joblib" in data["supported_model_formats"]
    assert ".csv" in data["supported_dataset_formats"]
    assert "binary_classification" in data["supported_task_types"]
    assert "ood_detection" in data["reliability_capabilities"]
    assert "reliability_fusion" in data["reliability_capabilities"]


def test_config_and_api_import_smoke():
    """Verify api.core.config settings and api.main module import cleanly without NameError."""
    from api.core.config import settings
    import api.main
    assert settings.API_TITLE == "AEGIS-X API"
    assert api.main.app is not None

