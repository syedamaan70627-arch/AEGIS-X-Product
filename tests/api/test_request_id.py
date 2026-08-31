"""
Tests for AEGIS-X Request-ID Middleware.
"""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_request_id_generated_automatically():
    """Test that X-Request-ID response header is generated when absent from request."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 10


def test_request_id_propagated_from_header():
    """Test that explicit X-Request-ID request header is propagated to response."""
    custom_id = "test-req-id-998877"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id
