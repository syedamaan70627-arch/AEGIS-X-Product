"""
Tests for Model Delete workflow, ownership security, dependency pre-flight, and active registry filtering.
"""

import io
import os
import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from api.main import app
from api.core.auth import get_current_user, UserContext

client = TestClient(app)


@pytest.fixture
def sample_model_file(tmp_path):
    """Creates a temporary trained LogisticRegression model saved as joblib."""
    clf = LogisticRegression()
    X = [[0, 0, 0], [1, 1, 1], [0, 1, 0], [1, 0, 1]]
    y = [0, 1, 0, 1]
    clf.fit(X, y)

    model_path = tmp_path / "delete_test_model.joblib"
    joblib.dump(clf, model_path)
    return model_path


def test_model_dependencies_and_deletion(sample_model_file):
    """Test dependency pre-flight inspection and safe delete execution."""
    # 1. Register a model
    with open(sample_model_file, "rb") as f:
        res_create = client.post(
            "/api/v1/models",
            data={"model_name": "Delete Target Model", "task_type": "binary_classification"},
            files={"file": ("delete_test_model.joblib", f, "application/octet-stream")},
        )
    assert res_create.status_code == 201
    model_id = res_create.json()["model_id"]

    # 2. Inspect dependencies
    res_deps = client.get(f"/api/v1/models/{model_id}/dependencies")
    assert res_deps.status_code == 200
    deps = res_deps.json()
    assert deps["model_id"] == model_id
    assert deps["model_name"] == "Delete Target Model"
    assert "uploaded_datasets" in deps
    assert "report_snapshots" in deps

    # 3. Model appears in list before delete
    res_list_before = client.get("/api/v1/models")
    assert res_list_before.status_code == 200
    ids_before = [m["model_id"] for m in res_list_before.json()["models"]]
    assert model_id in ids_before

    # 4. Perform deletion
    res_delete = client.delete(f"/api/v1/models/{model_id}")
    assert res_delete.status_code == 200
    del_data = res_delete.json()
    assert del_data["success"] is True
    assert del_data["model_id"] == model_id
    assert del_data["status"] == "deleted"

    # 5. Model no longer appears in active list
    res_list_after = client.get("/api/v1/models")
    assert res_list_after.status_code == 200
    ids_after = [m["model_id"] for m in res_list_after.json()["models"]]
    assert model_id not in ids_after

    # 6. GET /api/v1/models/{model_id} still retrieves model record for historical provenance with status 'deleted'
    res_get = client.get(f"/api/v1/models/{model_id}")
    assert res_get.status_code == 200
    get_data = res_get.json()
    assert get_data["status"] == "deleted"
    assert get_data["model_name"] == "Delete Target Model"


def test_model_deletion_ownership_security(sample_model_file):
    """Test that a non-owner cannot delete another user's model (returns 403 Forbidden)."""
    # 1. Register a model as local_dev_user
    with open(sample_model_file, "rb") as f:
        res_create = client.post(
            "/api/v1/models",
            data={"model_name": "Owner Protected Model", "task_type": "binary_classification"},
            files={"file": ("owner_model.joblib", f, "application/octet-stream")},
        )
    model_id = res_create.json()["model_id"]

    # 2. Override auth user to simulate attacker/other user
    def mock_attacker_user():
        return UserContext(user_id="attacker_user_99", email="attacker@example.com")

    app.dependency_overrides[get_current_user] = mock_attacker_user
    try:
        # Attacker tries to delete model
        res_attack = client.delete(f"/api/v1/models/{model_id}")
        assert res_attack.status_code == 403
        err = res_attack.json()
        assert err["error"]["code"] == "MODEL_NOT_OWNED"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_delete_nonexistent_model():
    """Test deleting a model that does not exist returns 404 Not Found."""
    res = client.delete("/api/v1/models/nonexistent-uuid-999")
    assert res.status_code == 404
    err = res.json()
    assert err["error"]["code"] == "MODEL_NOT_FOUND"
