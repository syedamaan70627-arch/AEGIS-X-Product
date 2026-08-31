"""
Tests for AEGIS-X API Reference State Fitting, Operational Analysis Execution, and Persistence.
"""

import io
import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from api.main import app

client = TestClient(app)


@pytest.fixture
def setup_registered_resources():
    """
    Sets up a registered classification model, reference dataset, and evaluation dataset.
    Returns dictionary with IDs.
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
        data={"model_name": "Analysis Test Model", "task_type": "binary_classification"},
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

    # 3. Upload Evaluation Dataset Label-Free (5 samples)
    eval_lf_rows = ["f1,f2,f3"]
    for i in range(5):
        eval_lf_rows.append(f"{0.2 + i*0.1},{0.2 + i*0.1},{0.2 + i*0.1}")
    eval_lf_csv = "\n".join(eval_lf_rows) + "\n"

    res_e_lf = client.post(
        "/api/v1/datasets",
        data={"model_id": model_id, "dataset_type": "EVALUATION"},
        files={"file": ("eval_lf.csv", io.BytesIO(eval_lf_csv.encode("utf-8")), "text/csv")},
    )
    eval_lf_dataset_id = res_e_lf.json()["dataset_id"]

    # 4. Upload Evaluation Dataset Label-Aware (5 samples with target)
    eval_la_rows = ["f1,f2,f3,target"]
    for i in range(5):
        eval_la_rows.append(f"{0.2 + i*0.1},{0.2 + i*0.1},{0.2 + i*0.1},{i%2}")
    eval_la_csv = "\n".join(eval_la_rows) + "\n"

    res_e_la = client.post(
        "/api/v1/datasets",
        data={"model_id": model_id, "dataset_type": "EVALUATION", "target_column": "target"},
        files={"file": ("eval_la.csv", io.BytesIO(eval_la_csv.encode("utf-8")), "text/csv")},
    )
    eval_la_dataset_id = res_e_la.json()["dataset_id"]

    return {
        "model_id": model_id,
        "reference_dataset_id": reference_dataset_id,
        "eval_lf_dataset_id": eval_lf_dataset_id,
        "eval_la_dataset_id": eval_la_dataset_id,
    }


def test_fit_reference_state_success(setup_registered_resources):
    """Test fitting reference baseline state."""
    res = setup_registered_resources
    response = client.post(f"/api/v1/models/{res['model_id']}/reference/{res['reference_dataset_id']}/fit")
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == res["model_id"]
    assert data["dataset_id"] == res["reference_dataset_id"]
    assert data["status"] == "fitted"
    assert data["num_samples"] == 10


def test_fit_reference_with_evaluation_dataset_fails(setup_registered_resources):
    """Test that fitting reference state using an EVALUATION dataset is rejected."""
    res = setup_registered_resources
    response = client.post(f"/api/v1/models/{res['model_id']}/reference/{res['eval_lf_dataset_id']}/fit")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "DATASET_VALIDATION_ERROR"
    assert "Reference fit requires 'REFERENCE' dataset" in data["error"]["message"]


def test_run_analysis_label_free(setup_registered_resources):
    """Test running AEGIS-X analysis on label-free evaluation dataset."""
    res = setup_registered_resources
    # Fit reference first
    client.post(f"/api/v1/models/{res['model_id']}/reference/{res['reference_dataset_id']}/fit")

    # Run analysis
    response = client.post(
        "/api/v1/analysis",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_lf_dataset_id"],
            "fusion_method": "stress_robust",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "analysis_id" in data
    assert data["status"] == "completed"

    # Individual signals MUST be present
    assert "ood" in data and data["ood"]["status"] == "AVAILABLE"
    assert "uncertainty" in data and data["uncertainty"]["status"] == "AVAILABLE"
    assert "drift" in data and data["drift"]["status"] == "AVAILABLE"
    assert "fusion" in data and data["fusion"]["status"] == "AVAILABLE"

    # Verify label-free behavior: diagnostics section is None
    assert data["diagnostics"] is None


def test_run_analysis_label_aware(setup_registered_resources):
    """Test running AEGIS-X analysis with true target labels produces retrospective diagnostics."""
    res = setup_registered_resources
    client.post(f"/api/v1/models/{res['model_id']}/reference/{res['reference_dataset_id']}/fit")

    response = client.post(
        "/api/v1/analysis",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_la_dataset_id"],
            "fusion_method": "original",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "completed"

    # Label-aware retrospective diagnostics MUST be present
    assert data["diagnostics"] is not None
    assert "accuracy" in data["diagnostics"]
    assert "error_rate" in data["diagnostics"]
    assert "num_failures" in data["diagnostics"]


def test_get_analysis_by_id(setup_registered_resources):
    """Test retrieving stored analysis result payload by analysis_id."""
    res = setup_registered_resources
    client.post(f"/api/v1/models/{res['model_id']}/reference/{res['reference_dataset_id']}/fit")

    res_analysis = client.post(
        "/api/v1/analysis",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_lf_dataset_id"],
        },
    )
    analysis_id = res_analysis.json()["analysis_id"]

    # Fetch result
    res_fetch = client.get(f"/api/v1/analysis/{analysis_id}")
    assert res_fetch.status_code == 200
    data = res_fetch.json()
    assert data["analysis_id"] == analysis_id
    assert data["model_id"] == res["model_id"]


def test_list_analyses_for_model(setup_registered_resources):
    """Test listing all analyses for a model."""
    res = setup_registered_resources
    client.post(f"/api/v1/models/{res['model_id']}/reference/{res['reference_dataset_id']}/fit")

    client.post(
        "/api/v1/analysis",
        json={
            "model_id": res["model_id"],
            "evaluation_dataset_id": res["eval_lf_dataset_id"],
        },
    )

    response = client.get(f"/api/v1/models/{res['model_id']}/analyses")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["analyses"][0]["model_id"] == res["model_id"]
