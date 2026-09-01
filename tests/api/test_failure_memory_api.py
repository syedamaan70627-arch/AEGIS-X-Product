"""
Tests for AEGIS-X API Failure Memory Endpoints & Matcher.
"""

import io
import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from api.main import app

client = TestClient(app)


@pytest.fixture
def setup_memory_resources():
    """Sets up a model, reference dataset, evaluation dataset, and generates fault test runs."""
    clf = LogisticRegression()
    X_train = [[float(i), float(i+1), float(i+2)] for i in range(10)]
    y_train = [i % 2 for i in range(10)]
    clf.fit(X_train, y_train)

    buf = io.BytesIO()
    joblib.dump(clf, buf)
    buf.seek(0)

    res_m = client.post(
        "/api/v1/models",
        data={"model_name": "Memory Test Model", "task_type": "binary_classification"},
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

    # Generate 3 fault injection runs to create condition profiles
    fault_ids = []
    for ftype in ["Sensor_Bias", "Gain_Error", "Stuck_At"]:
        res_f = client.post(
            "/api/v1/fault-tests",
            json={
                "model_id": model_id,
                "evaluation_dataset_id": eval_id,
                "fault_type": ftype,
                "severity": 0.4,
            },
        )
        fault_ids.append(res_f.json()["fault_test_id"])

    return {"model_id": model_id, "eval_id": eval_id, "fault_ids": fault_ids}


def test_build_failure_memory_success(setup_memory_resources):
    """Test building Failure Memory from fault injection runs."""
    res = setup_memory_resources
    response = client.post(
        f"/api/v1/failure-memory/{res['model_id']}/build",
        json={"model_id": res["model_id"], "fault_test_ids": res["fault_ids"], "n_clusters": 2},
    )
    assert response.status_code == 201
    data = response.json()
    assert "memory_id" in data
    assert data["status"] == "AVAILABLE"
    assert data["n_signatures"] > 0
    assert len(data["signatures"]) > 0


def test_match_failure_memory_query(setup_memory_resources):
    """Test querying pre-fitted Failure Memory centroids."""
    res = setup_memory_resources
    res_build = client.post(
        f"/api/v1/failure-memory/{res['model_id']}/build",
        json={"model_id": res["model_id"], "n_clusters": 2},
    )
    memory_id = res_build.json()["memory_id"]

    query_profile = {
        "mean_ood_risk": 0.3,
        "mean_uncertainty": 0.4,
        "mean_drift_score": 0.1,
        "mean_fused_risk": 0.35,
        "failure_rate": 0.2,
        "silent_failure_rate": 0.0,
    }

    res_match = client.post(
        f"/api/v1/failure-memory/{memory_id}/match",
        json={"query_profile": query_profile},
    )
    assert res_match.status_code == 200
    match_data = res_match.json()
    assert "matched_signature_id" in match_data
    assert "signature_distance" in match_data
    assert "is_known_pattern" in match_data


def test_build_failure_memory_without_body_model_id(setup_memory_resources):
    """Test building Failure Memory when request body omits model_id (matching frontend behavior)."""
    res = setup_memory_resources
    response = client.post(
        f"/api/v1/failure-memory/{res['model_id']}/build",
        json={"n_clusters": 3, "random_state": 42},
    )
    assert response.status_code == 201
    data = response.json()
    assert "memory_id" in data
    assert data["model_id"] == res["model_id"]
    assert data["status"] == "AVAILABLE"


def test_build_failure_memory_unknown_model_error():
    """Test building Failure Memory for non-existent model returns structured error."""
    response = client.post(
        "/api/v1/failure-memory/nonexistent-model-9999/build",
        json={"n_clusters": 3, "random_state": 42},
    )
    assert response.status_code in (400, 404)
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] in ("AEGIS_ERROR", "ANALYSIS_ERROR")
    assert "not found" in data["error"]["message"].lower()


