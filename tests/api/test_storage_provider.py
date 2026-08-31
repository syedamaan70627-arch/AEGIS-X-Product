"""
Tests for AEGIS-X Storage Providers (Local Filesystem & Supabase Storage).
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from api.storage.local_storage import LocalStorageProvider, PathTraversalError
from api.storage.supabase_storage import SupabaseStorageProvider


def test_local_storage_provider_scoped_save_and_load(tmp_path):
    """Test LocalStorageProvider saves and loads files under user-scoped directory."""
    provider = LocalStorageProvider(base_dir=tmp_path)
    user_id = "test_user_123"

    saved_path = provider.save_file("models/m1/model.joblib", b"dummy_content", user_id=user_id)
    assert f"users/{user_id}/models/m1/model.joblib" in saved_path.replace("\\", "/")

    loaded_content = provider.load_file("models/m1/model.joblib", user_id=user_id)
    assert loaded_content == b"dummy_content"

    # Test JSON save/load
    data = {"status": "ok", "value": 42}
    provider.save_json("results/r1/result.json", data, user_id=user_id)
    loaded_json = provider.load_json("results/r1/result.json", user_id=user_id)
    assert loaded_json == data


def test_local_storage_provider_path_traversal_defense(tmp_path):
    """Test path traversal attempts raise PathTraversalError."""
    provider = LocalStorageProvider(base_dir=tmp_path)
    with pytest.raises(PathTraversalError):
        provider.save_file("../../../etc/passwd", b"data", user_id="user1")


def test_supabase_storage_provider_mocked():
    """Test SupabaseStorageProvider object key scoping and HTTP API interactions."""
    mock_client = MagicMock()
    mock_res = MagicMock()
    mock_res.status_code = 201
    mock_client.post.return_value = mock_res

    mock_get_res = MagicMock()
    mock_get_res.status_code = 200
    mock_get_res.content = b'{"result": "success"}'
    mock_client.get.return_value = mock_get_res

    with patch("api.core.config.settings.SUPABASE_URL", "https://mock.supabase.co"), patch("api.core.config.settings.SUPABASE_SERVICE_ROLE_KEY", "service-key"):
        provider = SupabaseStorageProvider(client=mock_client)
        user_id = "user_abc"

        key = provider.save_file("models/m1/model.joblib", b"binary_data", user_id=user_id)
        assert key == "users/user_abc/models/m1/model.joblib"
        assert mock_client.post.called

        loaded_json = provider.load_json("results/r1/result.json", user_id=user_id)
        assert loaded_json == {"result": "success"}
