"""
AEGIS-X Module 14 Phase 6 REST API Integration Tests.

Tests for FastAPI Governance Router endpoints:
- POST /api/v1/governance/evaluate
- GET /api/v1/governance/{model_id}/status
- GET /api/v1/governance/{model_id}/history
"""

import io
import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from api.main import app

client = TestClient(app)


@pytest.fixture
def setup_governance_api_model():
    """Register a model file for API tests."""
    clf = LogisticRegression()
    X = [[0.0, 1.0], [1.0, 0.0]]
    y = [0, 1]
    clf.fit(X, y)

    buf = io.BytesIO()
    joblib.dump(clf, buf)
    buf.seek(0)

    res = client.post(
        "/api/v1/models",
        data={"model_name": "API Governance Model", "task_type": "binary_classification"},
        files={"file": ("model.joblib", buf, "application/octet-stream")},
    )
    assert res.status_code == 201
    return res.json()["model_id"]


def test_evaluate_governance_endpoint_success(setup_governance_api_model):
    """Test POST /api/v1/governance/evaluate with valid payload."""
    model_id = setup_governance_api_model

    payload = {
        "model_id": model_id,
        "dataset_id": "eval_dataset_001",
        "trajectory_id": "unit_001",
        "state_index": 0,
        "ood_score": 0.1,
        "uncertainty_score": 0.1,
        "drift_score": 0.05,
        "fused_risk": 0.12,
        "mode": "EVIDENCE_ONLY",
    }

    res = client.post("/api/v1/governance/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["model_id"] == model_id
    assert data["action"] in ["CONTINUE", "WATCH", "DEFER", "ESCALATE"]
    assert "certification_banner" in data
    assert "evidence_snapshot_hash" in data
    assert data["user_id"] == "local_dev_user"


def test_evaluate_governance_model_not_found():
    """Test POST /api/v1/governance/evaluate with non-existent model returns 404."""
    payload = {
        "model_id": "non_existent_model_id_999",
        "dataset_id": "eval_dataset_001",
        "ood_score": 0.1,
        "uncertainty_score": 0.1,
        "drift_score": 0.05,
        "fused_risk": 0.12,
    }

    res = client.post("/api/v1/governance/evaluate", json=payload)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]


def test_governance_status_endpoint(setup_governance_api_model):
    """Test GET /api/v1/governance/{model_id}/status."""
    model_id = setup_governance_api_model

    # Initial status
    res1 = client.get(f"/api/v1/governance/{model_id}/status")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["model_id"] == model_id
    assert data1["total_evaluations"] == 0

    # Perform evaluation
    payload = {
        "model_id": model_id,
        "dataset_id": "eval_dataset_001",
        "ood_score": 0.2,
        "uncertainty_score": 0.2,
        "drift_score": 0.1,
        "fused_risk": 0.2,
    }
    client.post("/api/v1/governance/evaluate", json=payload)

    # Status after evaluation
    res2 = client.get(f"/api/v1/governance/{model_id}/status")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total_evaluations"] == 1
    assert data2["latest_action"] is not None


def test_governance_history_pagination(setup_governance_api_model):
    """Test GET /api/v1/governance/{model_id}/history pagination."""
    model_id = setup_governance_api_model

    for i in range(5):
        payload = {
            "model_id": model_id,
            "dataset_id": "eval_dataset_001",
            "state_index": i,
            "ood_score": 0.1 * i,
            "uncertainty_score": 0.1 * i,
            "drift_score": 0.05 * i,
            "fused_risk": 0.1 * i,
        }
        client.post("/api/v1/governance/evaluate", json=payload)

    res = client.get(f"/api/v1/governance/{model_id}/history?limit=2&offset=1")
    assert res.status_code == 200
    data = res.json()

    assert data["model_id"] == model_id
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert len(data["evaluations"]) == 2


def test_governance_state_machine_transition_tracking(setup_governance_api_model):
    """Test state transition tracking over consecutive DEFER evaluations."""
    model_id = setup_governance_api_model

    # Evaluation 1: Low risk -> CONTINUE
    res1 = client.post(
        "/api/v1/governance/evaluate",
        json={
            "model_id": model_id,
            "dataset_id": "ds1",
            "state_index": 0,
            "ood_score": 0.0,
            "uncertainty_score": 0.0,
            "drift_score": 0.0,
            "fused_risk": 0.0,
        },
    )
    assert res1.json()["action"] == "CONTINUE"

    # Evaluation 2: High risk -> DEFER (Transition occurred from CONTINUE to DEFER)
    res2 = client.post(
        "/api/v1/governance/evaluate",
        json={
            "model_id": model_id,
            "dataset_id": "ds1",
            "state_index": 1,
            "ood_score": 0.8,
            "uncertainty_score": 0.8,
            "drift_score": 0.8,
            "fused_risk": 0.85,
        },
    )
    assert res2.json()["action"] in ["DEFER", "ESCALATE"]
    assert res2.json()["state_transition_occurred"] is True

    # Check status transitions count
    status_res = client.get(f"/api/v1/governance/{model_id}/status")
    assert status_res.json()["total_transitions"] >= 1
