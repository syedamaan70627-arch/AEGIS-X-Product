"""
Tests for AEGIS-X API Model Registry Endpoints & Security.
"""

import io
import tempfile
from pathlib import Path
import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from api.main import app

client = TestClient(app)


@pytest.fixture
def sample_model_file(tmp_path):
    """Creates a temporary trained LogisticRegression model saved as joblib."""
    clf = LogisticRegression()
    # Dummy data with 3 features
    X = [[0, 0, 0], [1, 1, 1], [0, 1, 0], [1, 0, 1]]
    y = [0, 1, 0, 1]
    clf.fit(X, y)

    model_path = tmp_path / "test_model.joblib"
    joblib.dump(clf, model_path)
    return model_path


def test_register_model_success(sample_model_file):
    """Test registering a valid joblib model."""
    with open(sample_model_file, "rb") as f:
        response = client.post(
            "/api/v1/models",
            data={
                "model_name": "Test Classifier",
                "task_type": "binary_classification",
                "description": "Synthetic test model",
            },
            files={"file": ("test_model.joblib", f, "application/octet-stream")},
        )

    assert response.status_code == 201
    data = response.json()
    assert "model_id" in data
    assert data["model_name"] == "Test Classifier"
    assert data["predict_supported"] is True
    assert data["predict_proba_supported"] is True
    assert data["n_features_in"] == 3
    assert data["status"] == "registered"


def test_get_model_details(sample_model_file):
    """Test retrieving model metadata by model_id."""
    with open(sample_model_file, "rb") as f:
        res_create = client.post(
            "/api/v1/models",
            data={"model_name": "Fetch Test Model", "task_type": "binary_classification"},
            files={"file": ("model.joblib", f, "application/octet-stream")},
        )
    model_id = res_create.json()["model_id"]

    res_get = client.get(f"/api/v1/models/{model_id}")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["model_id"] == model_id
    assert data["model_name"] == "Fetch Test Model"


def test_get_nonexistent_model():
    """Test GET /api/v1/models/{nonexistent_id} returns 404."""
    res = client.get("/api/v1/models/nonexistent-uuid-12345")
    assert res.status_code == 404


def test_register_model_invalid_extension():
    """Test registering a model with an unsupported extension (.txt)."""
    fake_file = io.BytesIO(b"not a joblib file")
    response = client.post(
        "/api/v1/models",
        data={"model_name": "Bad Ext Model", "task_type": "binary_classification"},
        files={"file": ("model.txt", fake_file, "text/plain")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "STORAGE_ERROR"
    assert "Unsupported model file extension" in data["error"]["message"]


def test_register_model_invalid_content(tmp_path):
    """Test registering a file with .joblib extension but corrupted contents."""
    bad_file_path = tmp_path / "corrupted.joblib"
    bad_file_path.write_bytes(b"invalid corrupt binary data")

    with open(bad_file_path, "rb") as f:
        response = client.post(
            "/api/v1/models",
            data={"model_name": "Corrupt Model", "task_type": "binary_classification"},
            files={"file": ("corrupted.joblib", f, "application/octet-stream")},
        )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "MODEL_LOAD_ERROR"


def test_path_traversal_filename_sanitized(sample_model_file):
    """Test that path traversal constructs in filenames are sanitized."""
    with open(sample_model_file, "rb") as f:
        response = client.post(
            "/api/v1/models",
            data={"model_name": "Path Traversal Test", "task_type": "binary_classification"},
            files={"file": ("../../etc/passwd.joblib", f, "application/octet-stream")},
        )
    assert response.status_code == 201
    data = response.json()
    # The filename should be sanitized to passwd.joblib, not ../../etc/passwd.joblib
    assert data["filename"] == "passwd.joblib"
