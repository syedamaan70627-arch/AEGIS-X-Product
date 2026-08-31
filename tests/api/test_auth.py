"""
Tests for AEGIS-X API Authentication & Identity Endpoints.
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
import httpx

from api.core.config import settings
from api.main import app

client = TestClient(app)


def test_auth_disabled_returns_dev_identity():
    """Test that local mode (AUTH_REQUIRED=false) returns default development user identity."""
    with patch.object(settings, "AUTH_REQUIRED", False):
        response = client.get("/api/v1/me")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "local_dev_user"
        assert data["email"] == "dev@aegis.local"
        assert data["authenticated"] is False


def test_auth_enabled_rejects_missing_bearer_token():
    """Test that production mode (AUTH_REQUIRED=true) rejects requests lacking Authorization header."""
    with patch.object(settings, "AUTH_REQUIRED", True):
        response = client.get("/api/v1/me")
        assert response.status_code == 401
        data = response.json()
        assert "Missing or malformed" in data["detail"]


def test_auth_enabled_rejects_invalid_token():
    """Test that invalid token fails authentication when AUTH_REQUIRED=true."""
    mock_res = MagicMock()
    mock_res.status_code = 401

    with patch.object(settings, "AUTH_REQUIRED", True), patch.object(settings, "SUPABASE_URL", "https://mock.supabase.co"), patch.object(settings, "SUPABASE_ANON_KEY", "mock-key"):
        with patch.object(httpx.AsyncClient, "get", return_value=mock_res):
            response = client.get("/api/v1/me", headers={"Authorization": "Bearer invalid-token"})
            assert response.status_code == 401


def test_auth_enabled_accepts_valid_token():
    """Test that valid token returns authenticated identity when AUTH_REQUIRED=true."""
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"id": "user-uuid-1234", "email": "user@example.com"}

    with patch.object(settings, "AUTH_REQUIRED", True), patch.object(settings, "SUPABASE_URL", "https://mock.supabase.co"), patch.object(settings, "SUPABASE_ANON_KEY", "mock-key"):
        with patch.object(httpx.AsyncClient, "get", return_value=mock_res):
            response = client.get("/api/v1/me", headers={"Authorization": "Bearer valid-token"})
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "user-uuid-1234"
            assert data["email"] == "user@example.com"
            assert data["authenticated"] is True
