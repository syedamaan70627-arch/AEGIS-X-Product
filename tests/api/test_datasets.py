"""
Tests for AEGIS-X API Dataset Registry Endpoints & Validation.
"""

import io
import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from api.main import app

client = TestClient(app)


@pytest.fixture
def registered_model():
    """Fixture that registers a 3-feature sklearn classification model and returns its model_id."""
    clf = LogisticRegression()
    X = [[0, 0, 0], [1, 1, 1], [0, 1, 0], [1, 0, 1]]
    y = [0, 1, 0, 1]
    clf.fit(X, y)

    buf = io.BytesIO()
    joblib.dump(clf, buf)
    buf.seek(0)

    res = client.post(
        "/api/v1/models",
        data={"model_name": "Dataset Test Model", "task_type": "binary_classification"},
        files={"file": ("model.joblib", buf, "application/octet-stream")},
    )
    return res.json()["model_id"]


def test_register_reference_dataset_success(registered_model):
    """Test uploading a valid reference CSV matching model's feature count."""
    csv_content = "f1,f2,f3,target\n0.1,0.2,0.3,0\n0.4,0.5,0.6,1\n0.7,0.8,0.9,0\n"
    csv_bytes = io.BytesIO(csv_content.encode("utf-8"))

    response = client.post(
        "/api/v1/datasets",
        data={
            "model_id": registered_model,
            "dataset_type": "REFERENCE",
            "target_column": "target",
        },
        files={"file": ("ref_data.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 201
    data = response.json()
    assert "dataset_id" in data
    assert data["model_id"] == registered_model
    assert data["dataset_type"] == "REFERENCE"
    assert data["num_samples"] == 3
    assert data["num_features"] == 3
    assert data["feature_names"] == ["f1", "f2", "f3"]
    assert data["has_target"] is True


def test_register_evaluation_dataset_label_free(registered_model):
    """Test uploading a valid evaluation CSV without target label column."""
    csv_content = "f1,f2,f3\n0.15,0.25,0.35\n0.45,0.55,0.65\n"
    csv_bytes = io.BytesIO(csv_content.encode("utf-8"))

    response = client.post(
        "/api/v1/datasets",
        data={
            "model_id": registered_model,
            "dataset_type": "EVALUATION",
        },
        files={"file": ("eval_data.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["dataset_type"] == "EVALUATION"
    assert data["has_target"] is False
    assert data["target_column"] is None


def test_register_empty_csv(registered_model):
    """Test uploading an empty CSV file returns 400 error."""
    csv_bytes = io.BytesIO(b"")

    response = client.post(
        "/api/v1/datasets",
        data={"model_id": registered_model, "dataset_type": "EVALUATION"},
        files={"file": ("empty.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "DATASET_VALIDATION_ERROR"


def test_register_duplicate_columns_csv(registered_model):
    """Test uploading a CSV with duplicate column names in header."""
    csv_content = "f1,f1,f3\n1,2,3\n"
    csv_bytes = io.BytesIO(csv_content.encode("utf-8"))

    response = client.post(
        "/api/v1/datasets",
        data={"model_id": registered_model, "dataset_type": "REFERENCE"},
        files={"file": ("dups.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "DATASET_VALIDATION_ERROR"
    assert "duplicate column names" in data["error"]["message"]


def test_register_feature_mismatch_csv(registered_model):
    """Test uploading a CSV with feature count mismatch against model."""
    # Model expects 3 features, CSV provides 2
    csv_content = "f1,f2\n1,2\n3,4\n"
    csv_bytes = io.BytesIO(csv_content.encode("utf-8"))

    response = client.post(
        "/api/v1/datasets",
        data={"model_id": registered_model, "dataset_type": "REFERENCE"},
        files={"file": ("mismatch.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "FEATURE_MISMATCH"
