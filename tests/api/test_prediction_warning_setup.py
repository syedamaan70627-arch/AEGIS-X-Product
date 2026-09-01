"""
Unit and API integration tests for Failure Prediction and Early Warning production setup workflows,
StorageService artifact persistence, capability readiness transitions, and runtime execution.
"""

import io
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from aegis.core.contracts import ReliabilityStatus
from aegis.prediction.engine import FailurePredictor
from aegis.warning.engine import EarlyWarningEngine
from api.core.config import settings
from api.main import app
from api.services.capability_service import CapabilityService
from api.services.storage_service import StorageService

client = TestClient(app)


@pytest.fixture
def sample_model_file(tmp_path):
    """Creates a temporary trained RandomForestClassifier model saved as joblib."""
    import joblib
    from sklearn.ensemble import RandomForestClassifier

    clf = RandomForestClassifier(n_estimators=10, random_state=42)
    X = [[0.1] * 30, [0.9] * 30, [0.2] * 30, [0.8] * 30]
    y = [0, 1, 0, 1]
    clf.fit(X, y)

    model_path = tmp_path / "test_model.joblib"
    joblib.dump(clf, model_path)
    return model_path


@pytest.fixture
def registered_model(sample_model_file):
    """Register a test model."""
    with open(sample_model_file, "rb") as f:
        res = client.post(
            "/api/v1/models",
            data={
                "model_name": "Setup Test Model",
                "task_type": "binary_classification",
                "description": "Test model for setup fixture",
            },
            files={"file": ("test_model.joblib", f, "application/octet-stream")},
        )
    assert res.status_code == 201
    return res.json()["model_id"]



@pytest.fixture
def raw_evaluation_dataset(registered_model):
    """Upload raw evaluation CSV (30 cancer features, missing temporal reliability signals)."""
    csv_content = ",".join([f"f_{i}" for i in range(30)]) + "\n"
    csv_content += ",".join(["0.5"] * 30) + "\n"

    files = {"file": ("eval_raw.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    data = {"model_id": registered_model, "dataset_type": "EVALUATION"}
    res = client.post("/api/v1/datasets", data=data, files=files)
    assert res.status_code == 201
    return res.json()["dataset_id"]


@pytest.fixture
def temporal_trajectory_dataset(registered_model):
    """Upload valid temporal degradation trajectory CSV."""
    with open(Path(__file__).parents[2] / "examples" / "sample_temporal_trajectory.csv", "rb") as f:
        csv_bytes = f.read()

    files = {"file": ("sample_temporal_trajectory.csv", io.BytesIO(csv_bytes), "text/csv")}
    data = {"model_id": registered_model, "dataset_type": "TEMPORAL_TRAJECTORY", "target_column": "Failure_Onset_Next"}
    res = client.post("/api/v1/datasets", data=data, files=files)
    assert res.status_code == 201
    return res.json()["dataset_id"]



def test_prediction_setup_rejects_raw_evaluation_csv(registered_model, raw_evaluation_dataset):
    """Requirement 1 & 3: Raw evaluation CSV without temporal reliability features is rejected."""
    res = client.post(
        f"/api/v1/failure-prediction/{registered_model}/fit",
        json={"trajectory_dataset_id": raw_evaluation_dataset},
    )
    assert res.status_code == 400
    data = res.json()
    assert "error" in data
    assert "trajectory_id" in data["error"]["message"].lower() or "cannot be used" in data["error"]["message"].lower() or "missing" in data["error"]["message"].lower()




def test_prediction_setup_valid_trajectory(registered_model, temporal_trajectory_dataset):
    """Requirements 2, 4, 5, 6, 7: Valid trajectory dataset fits FailurePredictor and persists artifact."""
    # Check initial capability status is REQUIRES_SETUP
    caps_before = CapabilityService.get_model_capabilities(registered_model)
    assert caps_before.capabilities["failure_prediction"].status == "REQUIRES_SETUP"

    # Fit prediction model
    res = client.post(
        f"/api/v1/failure-prediction/{registered_model}/fit",
        json={"trajectory_dataset_id": temporal_trajectory_dataset, "random_state": 42},
    )
    assert res.status_code == 200
    fit_data = res.json()
    assert fit_data["status"] == "fitted"
    assert fit_data["threshold"] is not None

    # Check capability transition to READY
    caps_after = CapabilityService.get_model_capabilities(registered_model)
    assert caps_after.capabilities["failure_prediction"].status == "READY"

    # Requirement 8 & 9: Verify artifact can be loaded via StorageService
    assert StorageService.has_prediction_artifact(registered_model)
    predictor = StorageService.load_prediction_artifact(registered_model)
    assert predictor.is_fitted


def test_prediction_setup_missing_trajectory_dataset_returns_error(registered_model):
    """Scientific Integrity Fix: Setup without trajectory_dataset_id must return HTTP 400 error."""
    res = client.post(f"/api/v1/failure-prediction/{registered_model}/fit", json={})
    assert res.status_code == 400
    data = res.json()
    assert "requires" in data["error"]["message"].lower() or "dataset" in data["error"]["message"].lower()


def test_warning_setup_missing_trajectory_dataset_returns_error(registered_model):
    """Scientific Integrity Fix: Early warning setup without trajectory_dataset_id must return HTTP 400 error."""
    res = client.post(f"/api/v1/early-warning/{registered_model}/fit", json={})
    assert res.status_code == 400
    data = res.json()
    assert "requires" in data["error"]["message"].lower() or "dataset" in data["error"]["message"].lower()


def test_warning_setup_valid_trajectory(registered_model, temporal_trajectory_dataset):
    """Requirements 13, 14, 15: Valid trajectory fits EarlyWarningEngine and updates capability to READY."""
    caps_before = CapabilityService.get_model_capabilities(registered_model)
    assert caps_before.capabilities["early_warning"].status == "REQUIRES_SETUP"

    res = client.post(
        f"/api/v1/early-warning/{registered_model}/fit",
        json={"trajectory_dataset_id": temporal_trajectory_dataset, "horizon_val": 3},
    )
    assert res.status_code == 200
    fit_data = res.json()
    assert fit_data["status"] == "fitted"
    assert fit_data["horizon_value"] == 3

    caps_after = CapabilityService.get_model_capabilities(registered_model)
    assert caps_after.capabilities["early_warning"].status == "READY"

    assert StorageService.has_warning_artifact(registered_model)
    engine = StorageService.load_warning_artifact(registered_model)
    assert engine.is_fitted


def test_prediction_and_warning_execution_after_setup(registered_model, temporal_trajectory_dataset):
    """Requirements 12 & 16: Prediction and warning execution succeed after setup."""
    # Fit prediction & warning engines with valid trajectory
    client.post(
        f"/api/v1/failure-prediction/{registered_model}/fit",
        json={"trajectory_dataset_id": temporal_trajectory_dataset},
    )
    client.post(
        f"/api/v1/early-warning/{registered_model}/fit",
        json={"trajectory_dataset_id": temporal_trajectory_dataset},
    )

    # Execute Prediction
    pred_res = client.post(
        "/api/v1/predictions/failure",
        json={"model_id": registered_model, "evaluation_dataset_id": temporal_trajectory_dataset},
    )
    assert pred_res.status_code == 200
    assert pred_res.json()["status"] == "AVAILABLE"

    # Query Warning
    warn_res = client.post(
        "/api/v1/warnings",
        json={"model_id": registered_model, "evaluation_dataset_id": temporal_trajectory_dataset},
    )
    assert warn_res.status_code == 200
    assert warn_res.json()["status"] == "AVAILABLE"


def test_setup_unauthorized_model_access():
    """Requirement 10: Owner isolation preserved."""
    res = client.post("/api/v1/failure-prediction/nonexistent-model-999/fit", json={"trajectory_dataset_id": "ds-1"})
    assert res.status_code in (400, 404)

