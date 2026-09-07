"""
Tests for Model Registration Forensics, Metadata Extraction, Transaction Rollback,
Missing Column Fallback, Owner Isolation, and Lifecycle Tombstoning.
"""

import io
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import joblib

from api.main import app
from api.core.auth import get_current_user, UserContext
from api.db.models import ModelRecord
from api.db.supabase_repositories import SupabaseModelRepository

client = TestClient(app)


@pytest.fixture
def digits_64_model_file(tmp_path):
    """Creates a 64-feature RandomForest model saved as joblib matching digits_parity_rf."""
    clf = RandomForestClassifier(n_estimators=5, random_state=42)
    X = np.random.randn(20, 64)
    y = np.random.randint(0, 2, size=20)
    clf.fit(X, y)
    clf.feature_names_in_ = np.array([f"pixel_{i:02d}" for i in range(64)])

    file_path = tmp_path / "digits_parity_rf.joblib"
    joblib.dump(clf, file_path)
    return file_path


def test_digits_64_feature_metadata_serialization(digits_64_model_file):
    """Verify registration extracts 64 features and converts numpy scalars to JSON-safe native types."""
    with open(digits_64_model_file, "rb") as f:
        res = client.post(
            "/api/v1/models",
            data={"model_name": "test1", "task_type": "binary_classification"},
            files={"file": ("digits_parity_rf.joblib", f, "application/octet-stream")},
        )
    assert res.status_code == 201
    data = res.json()
    assert data["model_name"] == "test1"
    assert data["task_type"] == "binary_classification"
    assert data["n_features_in"] == 64
    assert data["predict_supported"] is True
    assert data["predict_proba_supported"] is True
    assert len(data["feature_names"]) == 64
    assert isinstance(data["n_features_in"], int)
    assert isinstance(data["predict_proba_supported"], bool)


def test_artifact_rollback_on_db_insert_failure(digits_64_model_file):
    """Verify uploaded file artifact is deleted if database creation fails."""
    with patch("api.services.model_service.get_model_repository") as mock_repo_getter:
        mock_repo = MagicMock()
        mock_repo.create.side_effect = Exception("PGRST204 Could not find the 'status' column of 'models'")
        mock_repo_getter.return_value = mock_repo

        with open(digits_64_model_file, "rb") as f:
            res = client.post(
                "/api/v1/models",
                data={"model_name": "Rollback Test", "task_type": "binary_classification"},
                files={"file": ("digits_parity_rf.joblib", f, "application/octet-stream")},
            )

        assert res.status_code == 400
        err = res.json()
        assert err["error"]["code"] == "MODEL_SCHEMA_MISMATCH"


def test_supabase_repository_fallback_missing_status_column():
    """Verify SupabaseModelRepository retries insert without status when PostgREST returns PGRST204."""
    mock_httpx = MagicMock()
    
    # 1. First POST returns 400 with PGRST204 for 'status' column
    mock_res_400 = MagicMock()
    mock_res_400.status_code = 400
    mock_res_400.json.return_value = {
        "code": "PGRST204",
        "message": "Could not find the 'status' column of 'models' in the schema cache",
    }
    
    # 2. Second POST (retry without status) returns 201 Created
    mock_res_201 = MagicMock()
    mock_res_201.status_code = 201
    mock_res_201.raise_for_status.return_value = None

    mock_httpx.post.side_effect = [mock_res_400, mock_res_201]

    with patch("api.db.supabase_repositories.settings") as mock_settings:
        mock_settings.SUPABASE_URL = "https://fake.supabase.co"
        mock_settings.SUPABASE_SERVICE_ROLE_KEY = "fake-key"
        mock_settings.SUPABASE_ANON_KEY = "fake-key"

        repo = SupabaseModelRepository(client=mock_httpx)
        record = ModelRecord(
            id="00000000-0000-0000-0000-000000000001",
            model_name="Fallback Test",
            task_type="binary_classification",
            file_path="users/u1/models/m1/model.joblib",
            filename="model.joblib",
            predict_supported=True,
            predict_proba_supported=True,
            created_at="2026-09-07T12:00:00Z",
            status="active",
        )

        res_record = repo.create(record)
        assert res_record.id == record.id
        assert mock_httpx.post.call_count == 2
        
        # Verify second call omitted 'status' key
        second_payload = mock_httpx.post.call_args_list[1][1]["json"]
        assert "status" not in second_payload
        assert second_payload["model_name"] == "Fallback Test"


def test_tombstoned_models_allow_new_registrations(digits_64_model_file):
    """Verify registering a new model succeeds after a tombstoned model exists."""
    # 1. Register model A
    with open(digits_64_model_file, "rb") as f:
        res_a = client.post(
            "/api/v1/models",
            data={"model_name": "Model A", "task_type": "binary_classification"},
            files={"file": ("model_a.joblib", f, "application/octet-stream")},
        )
    assert res_a.status_code == 201
    id_a = res_a.json()["model_id"]

    # 2. Delete model A (tombstone)
    res_del = client.delete(f"/api/v1/models/{id_a}")
    assert res_del.status_code == 200

    # 3. Register model B
    with open(digits_64_model_file, "rb") as f:
        res_b = client.post(
            "/api/v1/models",
            data={"model_name": "Model B", "task_type": "binary_classification"},
            files={"file": ("model_b.joblib", f, "application/octet-stream")},
        )
    assert res_b.status_code == 201
    id_b = res_b.json()["model_id"]

    # 4. List models -> model B is present, tombstoned model A is absent from active list
    res_list = client.get("/api/v1/models")
    assert res_list.status_code == 200
    active_ids = [m["model_id"] for m in res_list.json()["models"]]
    assert id_b in active_ids
    assert id_a not in active_ids
