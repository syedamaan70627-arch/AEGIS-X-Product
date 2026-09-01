"""
Tests for AEGIS-X Reference Fit Atomicity, Dataset Type Validation, CORS Exception Handling, and Dataset Deletion.
"""

from unittest.mock import MagicMock, patch
import numpy as np
import pytest
from fastapi.testclient import TestClient

from aegis.core.exceptions import DatasetValidationError
from api.core.auth import UserContext, get_current_user
from api.db.models import DatasetRecord, ModelRecord
from api.main import app
from api.services.analysis_service import AnalysisService, AnalysisServiceError

client = TestClient(app, raise_server_exceptions=False)


def test_reference_fit_rejects_evaluation_dataset():
    """Test that fit_reference_state fails when dataset_type is EVALUATION."""
    mock_model = ModelRecord(
        id="m-1",
        user_id="dev",
        model_name="Test Model",
        task_type="binary_classification",
        description=None,
        file_path="models/m-1/model.joblib",
        filename="model.joblib",
        predict_supported=True,
        predict_proba_supported=True,
        n_features_in=2,
        classes=[0, 1],
        feature_names=["f1", "f2"],
        created_at="2026-09-01T00:00:00Z",
    )
    mock_eval_dataset = DatasetRecord(
        id="d-eval",
        user_id="dev",
        model_id="m-1",
        dataset_type="EVALUATION",
        file_path="datasets/d-eval/eval.csv",
        filename="eval.csv",
        target_column=None,
        num_samples=100,
        num_features=2,
        feature_names=["f1", "f2"],
        has_target=False,
        created_at="2026-09-01T00:00:00Z",
    )

    with patch("api.services.analysis_service.get_model_repository") as mock_m_repo, patch(
        "api.services.analysis_service.get_dataset_repository"
    ) as mock_d_repo:

        mock_m_repo.return_value.get_by_id.return_value = mock_model
        mock_d_repo.return_value.get_by_id.return_value = mock_eval_dataset

        with pytest.raises(DatasetValidationError) as exc_info:
            AnalysisService.fit_reference_state("m-1", "d-eval", user_id="dev")

        assert "requires 'REFERENCE' dataset" in str(exc_info.value)


def test_reference_fit_atomicity_on_storage_failure():
    """Test that failure during artifact saving does not persist a corrupt reference state record."""
    mock_model = ModelRecord(
        id="m-1",
        user_id="dev",
        model_name="Test Model",
        task_type="binary_classification",
        description=None,
        file_path="models/m-1/model.joblib",
        filename="model.joblib",
        predict_supported=True,
        predict_proba_supported=True,
        n_features_in=2,
        classes=[0, 1],
        feature_names=["f1", "f2"],
        created_at="2026-09-01T00:00:00Z",
    )
    mock_ref_dataset = DatasetRecord(
        id="d-ref",
        user_id="dev",
        model_id="m-1",
        dataset_type="REFERENCE",
        file_path="datasets/d-ref/ref.csv",
        filename="ref.csv",
        target_column=None,
        num_samples=10,
        num_features=2,
        feature_names=["f1", "f2"],
        has_target=False,
        created_at="2026-09-01T00:00:00Z",
    )

    mock_ref_repo = MagicMock()

    with patch("api.services.analysis_service.get_model_repository") as mock_m_repo, patch(
        "api.services.analysis_service.get_dataset_repository"
    ) as mock_d_repo, patch(
        "api.services.analysis_service.get_reference_state_repository", return_value=mock_ref_repo
    ), patch(
        "api.services.analysis_service.StorageService.load_model_adapter"
    ), patch(
        "api.services.analysis_service.StorageService.load_dataset"
    ) as mock_load_ds, patch(
        "api.services.analysis_service.StorageService.save_joblib_artifact", side_effect=RuntimeError("Storage connection dropped")
    ):

        mock_m_repo.return_value.get_by_id.return_value = mock_model
        mock_d_repo.return_value.get_by_id.return_value = mock_ref_dataset

        ds_obj = MagicMock()
        ds_obj.X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0], [9.0, 10.0]])
        ds_obj.y = None
        ds_obj.feature_names = ["f1", "f2"]
        ds_obj.num_samples = 5
        mock_load_ds.return_value = ds_obj

        with pytest.raises(AnalysisServiceError) as exc_info:
            AnalysisService.fit_reference_state("m-1", "d-ref", user_id="dev")

        assert "Storage connection dropped" in str(exc_info.value)
        # Ensure database save_or_update was NEVER called when artifact saving failed!
        mock_ref_repo.save_or_update.assert_not_called()


def test_unhandled_exception_returns_structured_json_with_cors():
    """Test that unhandled backend exceptions return HTTP 500 JSON response with CORS headers."""
    app.dependency_overrides[get_current_user] = lambda: UserContext(user_id="test_user", email="test@example.com")
    try:
        with patch("api.routes.models.AnalysisService.fit_reference_state", side_effect=RuntimeError("Unexpected Railway worker error")):
            response = client.post("/api/v1/models/m-1/reference/d-1/fit", headers={"Origin": "http://localhost:3000"})
            assert response.status_code == 500
            data = response.json()
            assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
            assert "Unexpected Railway worker error" in data["error"]["message"]
            assert "access-control-allow-origin" in response.headers
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_dataset_deletion_endpoint():
    """Test that DELETE /api/v1/datasets/{dataset_id} deletes the dataset record."""
    app.dependency_overrides[get_current_user] = lambda: UserContext(user_id="test_user", email="test@example.com")
    try:
        with patch("api.services.dataset_service.DatasetService.delete_dataset", return_value=True):
            response = client.delete("/api/v1/datasets/d-delete-123")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "deleted"
            assert data["dataset_id"] == "d-delete-123"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
