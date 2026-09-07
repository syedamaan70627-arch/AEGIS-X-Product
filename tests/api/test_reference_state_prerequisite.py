"""
AEGIS-X API Reference State Prerequisite Regression Tests.
"""

import io
import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from api.main import app

client = TestClient(app)


@pytest.fixture
def setup_prerequisite_test_resources():
    """
    Sets up a registered model, reference dataset, and evaluation dataset.
    """
    # 1. Register Model (3 features)
    clf = LogisticRegression()
    X_train = [[0, 0, 0], [1, 1, 1], [0, 1, 0], [1, 0, 1], [0.5, 0.5, 0.5]]
    y_train = [0, 1, 0, 1, 0]
    clf.fit(X_train, y_train)

    buf = io.BytesIO()
    joblib.dump(clf, buf)
    buf.seek(0)

    res_m = client.post(
        "/api/v1/models",
        data={"model_name": "Prerequisite Test Model", "task_type": "binary_classification"},
        files={"file": ("model.joblib", buf, "application/octet-stream")},
    )
    model_id = res_m.json()["model_id"]

    # 2. Upload Reference Dataset (10 samples, 3 features)
    ref_rows = ["f1,f2,f3,target"]
    for i in range(10):
        ref_rows.append(f"{i*0.1},{i*0.1},{i*0.1},{i%2}")
    ref_csv = "\n".join(ref_rows) + "\n"

    res_r = client.post(
        "/api/v1/datasets",
        data={"model_id": model_id, "dataset_type": "REFERENCE", "target_column": "target"},
        files={"file": ("ref.csv", io.BytesIO(ref_csv.encode("utf-8")), "text/csv")},
    )
    reference_dataset_id = res_r.json()["dataset_id"]

    # 3. Upload Evaluation Dataset (5 samples, 3 features)
    eval_rows = ["f1,f2,f3"]
    for i in range(5):
        eval_rows.append(f"{0.2 + i*0.1},{0.2 + i*0.1},{0.2 + i*0.1}")
    eval_csv = "\n".join(eval_rows) + "\n"

    res_e = client.post(
        "/api/v1/datasets",
        data={"model_id": model_id, "dataset_type": "EVALUATION"},
        files={"file": ("eval.csv", io.BytesIO(eval_csv.encode("utf-8")), "text/csv")},
    )
    eval_dataset_id = res_e.json()["dataset_id"]

    return {
        "model_id": model_id,
        "reference_dataset_id": reference_dataset_id,
        "eval_dataset_id": eval_dataset_id,
    }


def test_capabilities_shows_requires_setup_before_fitting(setup_prerequisite_test_resources):
    """Verify capabilities endpoint reports REQUIRES_SETUP for core_analysis before fitting."""
    res = setup_prerequisite_test_resources
    response = client.get(f"/api/v1/models/{res['model_id']}/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == res["model_id"]
    assert data["capabilities"]["core_analysis"]["status"] == "REQUIRES_SETUP"


def test_analysis_fails_if_reference_not_fitted(setup_prerequisite_test_resources):
    """Verify running analysis before fitting reference state returns explicit prerequisite error."""
    res = setup_prerequisite_test_resources
    response = client.post(
        "/api/v1/analysis",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_dataset_id"],
            "fusion_method": "stress_robust",
        },
    )
    assert response.status_code == 400
    data = response.json()
    err_msg = data.get("error", {}).get("message") or data.get("detail") or ""
    assert "has no fitted reference state" in err_msg


def test_reference_fit_updates_capabilities_to_ready(setup_prerequisite_test_resources):
    """Verify fitting reference state successfully transitions core_analysis capability to READY."""
    res = setup_prerequisite_test_resources
    # Fit reference state
    fit_res = client.post(f"/api/v1/models/{res['model_id']}/reference/{res['reference_dataset_id']}/fit")
    assert fit_res.status_code == 200
    assert fit_res.json()["status"] == "fitted"

    # Query capabilities
    cap_res = client.get(f"/api/v1/models/{res['model_id']}/capabilities")
    assert cap_res.status_code == 200
    assert cap_res.json()["capabilities"]["core_analysis"]["status"] == "READY"

    # Now analysis succeeds
    analysis_res = client.post(
        "/api/v1/analysis",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_dataset_id"],
            "fusion_method": "stress_robust",
        },
    )
    assert analysis_res.status_code == 201
    assert analysis_res.json()["status"] == "completed"


def test_cannot_fit_reference_with_evaluation_dataset(setup_prerequisite_test_resources):
    """Verify that using an EVALUATION dataset for reference fitting is strictly rejected."""
    res = setup_prerequisite_test_resources
    fit_res = client.post(f"/api/v1/models/{res['model_id']}/reference/{res['eval_dataset_id']}/fit")
    assert fit_res.status_code == 400
    err_msg = fit_res.json().get("error", {}).get("message") or fit_res.json().get("detail") or ""
    assert "requires 'REFERENCE' dataset" in err_msg
