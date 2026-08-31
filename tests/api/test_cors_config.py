"""
Tests for AEGIS-X CORS Configuration.
"""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_cors_preflight_headers():
    """Test CORS preflight request returns Access-Control-Allow-Origin."""
    response = client.options(
        "/api/v1/status",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
