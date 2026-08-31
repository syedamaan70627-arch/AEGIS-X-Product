"""
Tests for AEGIS-X Model Reliability Capabilities Endpoint.
"""

import io
import joblib
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from api.main import app

client = TestClient(app)


def test_model_capabilities_endpoint():
    """Test GET /api/v1/models/{model_id}/capabilities."""
    clf = LogisticRegression()
    clf.fit([[1, 2, 3], [4, 5, 6]], [0, 1])

    buf = io.BytesIO()
    joblib.dump(clf, buf)
    buf.seek(0)

    res_m = client.post(
        "/api/v1/models",
        data={"model_name": "Capabilities Test Model", "task_type": "binary_classification"},
        files={"file": ("model.joblib", buf, "application/octet-stream")},
    )
    model_id = res_m.json()["model_id"]

    response = client.get(f"/api/v1/models/{model_id}/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == model_id

    caps = data["capabilities"]
    assert "core_analysis" in caps
    assert "stress_testing" in caps
    assert "fault_testing" in caps
    assert "failure_memory" in caps
    assert "failure_prediction" in caps
    assert "early_warning" in caps

    # Unfitted reference state -> REQUIRES_SETUP
    assert caps["core_analysis"]["status"] == "REQUIRES_SETUP"
    assert caps["failure_prediction"]["status"] == "REQUIRES_SETUP"
    assert caps["early_warning"]["status"] == "REQUIRES_SETUP"
