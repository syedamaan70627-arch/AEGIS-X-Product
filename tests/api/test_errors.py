"""
Tests for API Exception Handlers and Security Boundaries.
"""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_analysis_unfitted_model_error():
    """Test running analysis when reference state has not been fitted."""
    # First create model and evaluation dataset
    import io, joblib
    from sklearn.linear_model import LogisticRegression

    clf = LogisticRegression()
    clf.fit([[1, 2], [3, 4]], [0, 1])
    buf = io.BytesIO()
    joblib.dump(clf, buf)
    buf.seek(0)

    res_m = client.post(
        "/api/v1/models",
        data={"model_name": "Unfitted Test Model", "task_type": "binary_classification"},
        files={"file": ("model.joblib", buf, "application/octet-stream")},
    )
    model_id = res_m.json()["model_id"]

    res_e = client.post(
        "/api/v1/datasets",
        data={"model_id": model_id, "dataset_type": "EVALUATION"},
        files={"file": ("eval.csv", io.BytesIO(b"f1,f2\n1,2\n3,4\n"), "text/csv")},
    )
    eval_id = res_e.json()["dataset_id"]

    # Trigger analysis without fitting reference state
    response = client.post(
        "/api/v1/analysis",
        json={"model_id": model_id, "evaluation_dataset_id": eval_id},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "ANALYSIS_ERROR"
    assert "has no fitted reference state" in data["error"]["message"]


def test_nonexistent_analysis_404():
    """Test GET /api/v1/analysis/{nonexistent_id} returns 404."""
    response = client.get("/api/v1/analysis/nonexistent-id-999")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "ANALYSIS_ERROR"
