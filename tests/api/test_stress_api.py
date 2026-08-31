"""
Tests for AEGIS-X API Stress Lab Endpoints.
"""

import io
import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from api.main import app

client = TestClient(app)


@pytest.fixture
def setup_stress_resources():
    """Sets up a registered model, reference dataset (fitted), and evaluation dataset."""
    clf = LogisticRegression()
    X_train = [[float(i), float(i+1), float(i+2)] for i in range(10)]
    y_train = [i % 2 for i in range(10)]
    clf.fit(X_train, y_train)

    buf = io.BytesIO()
    joblib.dump(clf, buf)
    buf.seek(0)

    res_m = client.post(
        "/api/v1/models",
        data={"model_name": "Stress Test Model", "task_type": "binary_classification"},
        files={"file": ("model.joblib", buf, "application/octet-stream")},
    )
    model_id = res_m.json()["model_id"]

    ref_rows = ["f1,f2,f3,target"]
    for i in range(10):
        ref_rows.append(f"{i*1.0},{i*1.0 + 1.0},{i*1.0 + 2.0},{i%2}")
    ref_csv = "\n".join(ref_rows) + "\n"

    res_r = client.post(
        "/api/v1/datasets",
        data={"model_id": model_id, "dataset_type": "REFERENCE", "target_column": "target"},
        files={"file": ("ref.csv", io.BytesIO(ref_csv.encode("utf-8")), "text/csv")},
    )
    ref_id = res_r.json()["dataset_id"]

    # Fit reference state
    client.post(f"/api/v1/models/{model_id}/reference/{ref_id}/fit")

    eval_rows = ["f1,f2,f3,target"]
    for i in range(5):
        eval_rows.append(f"{i*0.5},{i*0.5 + 0.5},{i*0.5 + 1.0},{i%2}")
    eval_csv = "\n".join(eval_rows) + "\n"

    res_e = client.post(
        "/api/v1/datasets",
        data={"model_id": model_id, "dataset_type": "EVALUATION", "target_column": "target"},
        files={"file": ("eval.csv", io.BytesIO(eval_csv.encode("utf-8")), "text/csv")},
    )
    eval_id = res_e.json()["dataset_id"]

    return {"model_id": model_id, "ref_id": ref_id, "eval_id": eval_id}


@pytest.mark.parametrize("stress_type", ["Gaussian_Noise", "Feature_Dropout", "Feature_Permutation", "Combined_Stress"])
def test_run_stress_test_families(setup_stress_resources, stress_type):
    """Test running each supported stress family."""
    res = setup_stress_resources
    response = client.post(
        "/api/v1/stress-tests",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_id"],
            "stress_type": stress_type,
            "severity": 0.3,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "stress_test_id" in data
    assert data["stress_type"] == stress_type
    assert data["status"] == "AVAILABLE"
    assert "risk_delta" in data
    assert "accuracy_delta" in data


def test_invalid_stress_type(setup_stress_resources):
    """Test invalid stress_type is rejected with 400."""
    res = setup_stress_resources
    response = client.post(
        "/api/v1/stress-tests",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_id"],
            "stress_type": "NonExistentNoise",
            "severity": 0.3,
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "DATASET_VALIDATION_ERROR"


def test_invalid_stress_severity(setup_stress_resources):
    """Test severity out of range [0.0, 1.0] is rejected."""
    res = setup_stress_resources
    response = client.post(
        "/api/v1/stress-tests",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_id"],
            "stress_type": "Gaussian_Noise",
            "severity": 1.5,
        },
    )
    assert response.status_code == 400


def test_get_stress_test_and_list(setup_stress_resources):
    """Test retrieving stress test payload by ID and listing by model."""
    res = setup_stress_resources
    res_run = client.post(
        "/api/v1/stress-tests",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_id"],
            "stress_type": "Gaussian_Noise",
            "severity": 0.2,
        },
    )
    stress_test_id = res_run.json()["stress_test_id"]

    res_get = client.get(f"/api/v1/stress-tests/{stress_test_id}")
    assert res_get.status_code == 200
    assert res_get.json()["stress_test_id"] == stress_test_id

    res_list = client.get(f"/api/v1/models/{res['model_id']}/stress-tests")
    assert res_list.status_code == 200
    assert res_list.json()["total"] >= 1
