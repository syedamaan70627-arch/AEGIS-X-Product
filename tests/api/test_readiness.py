"""
Tests for AEGIS-X Readiness Probe Endpoint.
"""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_readiness_probe_local():
    """Test readiness probe in default local mode."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"
    assert data["database"] == "HEALTHY"
    assert data["storage"] == "HEALTHY"
    assert data["auth"] in ("DISABLED", "REQUIRED", "HEALTHY")
