"""
Tests for AEGIS-X API Fault Injection & Failure Explorer Endpoints.
"""

import io
import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from api.main import app

client = TestClient(app)


@pytest.fixture
def setup_fault_resources():
    """Sets up a registered model, fitted reference dataset, and label-aware + label-free evaluation datasets."""
    clf = LogisticRegression()
    X_train = [[float(i), float(i+1), float(i+2)] for i in range(10)]
    y_train = [i % 2 for i in range(10)]
    clf.fit(X_train, y_train)

    buf = io.BytesIO()
    joblib.dump(clf, buf)
    buf.seek(0)

    res_m = client.post(
        "/api/v1/models",
        data={"model_name": "Fault Test Model", "task_type": "binary_classification"},
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

    # Label-aware evaluation
    eval_la_rows = ["f1,f2,f3,target"]
    for i in range(5):
        eval_la_rows.append(f"{i*0.5},{i*0.5 + 0.5},{i*0.5 + 1.0},{i%2}")
    eval_la_csv = "\n".join(eval_la_rows) + "\n"

    res_e_la = client.post(
        "/api/v1/datasets",
        data={"model_id": model_id, "dataset_type": "EVALUATION", "target_column": "target"},
        files={"file": ("eval_la.csv", io.BytesIO(eval_la_csv.encode("utf-8")), "text/csv")},
    )
    eval_la_id = res_e_la.json()["dataset_id"]

    # Label-free evaluation
    eval_lf_rows = ["f1,f2,f3"]
    for i in range(5):
        eval_lf_rows.append(f"{i*0.5},{i*0.5 + 0.5},{i*0.5 + 1.0}")
    eval_lf_csv = "\n".join(eval_lf_rows) + "\n"

    res_e_lf = client.post(
        "/api/v1/datasets",
        data={"model_id": model_id, "dataset_type": "EVALUATION"},
        files={"file": ("eval_lf.csv", io.BytesIO(eval_lf_csv.encode("utf-8")), "text/csv")},
    )
    eval_lf_id = res_e_lf.json()["dataset_id"]

    return {"model_id": model_id, "eval_la_id": eval_la_id, "eval_lf_id": eval_lf_id}


@pytest.mark.parametrize("fault_type", ["Sensor_Bias", "Gain_Error", "Stuck_At", "Channel_Swap", "Sign_Inversion"])
def test_run_fault_injection_families(setup_fault_resources, fault_type):
    """Test injecting each supported fault family."""
    res = setup_fault_resources
    kwargs = {}
    if fault_type == "Channel_Swap":
        kwargs["feature_pair"] = ["f1", "f2"]
    elif fault_type == "Stuck_At":
        kwargs["stuck_value"] = 0.0

    response = client.post(
        "/api/v1/fault-tests",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_la_id"],
            "fault_type": fault_type,
            "severity": 0.3,
            "affected_features": ["f1"],
            **kwargs,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "fault_test_id" in data
    assert data["fault_type"] == fault_type
    assert data["status"] == "AVAILABLE"


def test_invalid_affected_feature(setup_fault_resources):
    """Test specifying a non-existent feature name is rejected."""
    res = setup_fault_resources
    response = client.post(
        "/api/v1/fault-tests",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_la_id"],
            "fault_type": "Sensor_Bias",
            "severity": 0.3,
            "affected_features": ["non_existent_column"],
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "DATASET_VALIDATION_ERROR"


def test_failure_explorer_label_aware_vs_label_free(setup_fault_resources):
    """Test Failure Explorer outputs for label-aware vs label-free runs."""
    res = setup_fault_resources

    # 1. Label-aware fault test
    res_la = client.post(
        "/api/v1/fault-tests",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_la_id"],
            "fault_type": "Sensor_Bias",
            "severity": 0.4,
            "affected_features": ["f1"],
        },
    )
    fault_la_id = res_la.json()["fault_test_id"]

    res_fe_la = client.get(f"/api/v1/fault-tests/{fault_la_id}/failures")
    assert res_fe_la.status_code == 200
    fe_la_data = res_fe_la.json()
    assert fe_la_data["is_label_aware"] is True
    assert fe_la_data["silent_failure_status"] == "AVAILABLE"
    assert fe_la_data["total_failures"] is not None

    # 2. Label-free fault test
    res_lf = client.post(
        "/api/v1/fault-tests",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_lf_id"],
            "fault_type": "Gain_Error",
            "severity": 0.4,
            "affected_features": ["f1"],
        },
    )
    fault_lf_id = res_lf.json()["fault_test_id"]

    res_fe_lf = client.get(f"/api/v1/fault-tests/{fault_lf_id}/failures")
    assert res_fe_lf.status_code == 200
    fe_lf_data = res_fe_lf.json()
    assert fe_lf_data["is_label_aware"] is False
    assert fe_lf_data["silent_failure_status"] == "NOT_AVAILABLE"
    assert fe_lf_data["total_failures"] is None
