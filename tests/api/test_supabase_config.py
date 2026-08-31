"""
Tests for AEGIS-X Supabase Missing Credential Readiness Handling.
"""

from unittest.mock import patch
from fastapi.testclient import TestClient
from api.core.config import settings
from api.main import app

client = TestClient(app)


def test_supabase_backend_unconfigured_readiness():
    """Test that missing Supabase credentials when DATABASE_BACKEND=supabase mark readiness DEGRADED/UNCONFIGURED."""
    with patch.object(settings, "DATABASE_BACKEND", "supabase"), patch.object(settings, "SUPABASE_URL", None):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DEGRADED"
        assert "UNCONFIGURED" in data["database"]
