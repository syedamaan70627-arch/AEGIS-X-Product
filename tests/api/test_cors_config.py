"""
Tests for AEGIS-X CORS Configuration (Production & Vercel Preview Regex).
"""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_cors_preflight_local_origin():
    """Test CORS preflight request for local development origin."""
    response = client.options(
        "/api/v1/status",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_preflight_production_canonical_origin():
    """Test CORS preflight request for canonical production origin https://aegis-x-product.vercel.app."""
    response = client.options(
        "/api/v1/status",
        headers={
            "Origin": "https://aegis-x-product.vercel.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://aegis-x-product.vercel.app"


def test_cors_preflight_approved_vercel_preview_origin():
    """Test CORS preflight for project-specific Vercel preview domain family."""
    preview_origin = "https://aegis-x-product-abc123xyz-syedamaan70627-4156s-projects.vercel.app"
    response = client.options(
        "/api/v1/status",
        headers={
            "Origin": preview_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == preview_origin


def test_cors_preflight_unrelated_vercel_domain_blocked():
    """Test CORS preflight for an arbitrary or malicious unrelated Vercel domain is blocked."""
    unrelated_origin = "https://unrelated-malicious-app.vercel.app"
    response = client.options(
        "/api/v1/status",
        headers={
            "Origin": unrelated_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    # Blocked origin does NOT return access-control-allow-origin header for that origin
    allow_origin = response.headers.get("access-control-allow-origin")
    assert allow_origin != unrelated_origin
