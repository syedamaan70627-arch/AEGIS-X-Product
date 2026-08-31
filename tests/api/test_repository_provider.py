"""
Tests for AEGIS-X Repository Factory & Provider Abstraction.
"""

from unittest.mock import patch
from api.core.config import settings
from api.core.dependencies import get_model_repository
from api.db.repositories import ModelRepository
from api.db.supabase_repositories import SupabaseModelRepository


def test_repository_factory_sqlite():
    """Test factory returns SQLite ModelRepository when DATABASE_BACKEND=sqlite."""
    with patch.object(settings, "DATABASE_BACKEND", "sqlite"):
        repo = get_model_repository()
        assert isinstance(repo, ModelRepository)


def test_repository_factory_supabase():
    """Test factory returns SupabaseModelRepository when DATABASE_BACKEND=supabase."""
    with patch.object(settings, "DATABASE_BACKEND", "supabase"), patch.object(settings, "SUPABASE_URL", "https://mock.supabase.co"), patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", "key"):
        repo = get_model_repository()
        assert isinstance(repo, SupabaseModelRepository)
