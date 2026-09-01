"""
Tests for AEGIS-X API Early Warning Endpoints.
"""

import io
import joblib
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression

from aegis.warning.engine import EarlyWarningEngine
from api.core.config import settings
from api.main import app

client = TestClient(app)


@pytest.fixture
def setup_warning_resources():
    """Sets up a registered model and evaluation dataset with early warning features."""
    clf = LogisticRegression()
    X_train = [[float(i), float(i+1), float(i+2), float(i+3)] for i in range(10)]
    y_train = [i % 2 for i in range(10)]
    clf.fit(X_train, y_train)

    buf = io.BytesIO()
    joblib.dump(clf, buf)
    buf.seek(0)

    res_m = client.post(
        "/api/v1/models",
        data={"model_name": "Warning Test Model", "task_type": "binary_classification"},
        files={"file": ("model.joblib", buf, "application/octet-stream")},
    )
    assert res_m.status_code == 201
    model_id = res_m.json()["model_id"]

    eval_rows = ["trajectory_id,step,ood_risk,uncertainty_risk,drift_risk,fused_risk,Failure_Within_3"]
    for i in range(5):
        eval_rows.append(f"0,{i},{i*0.1},{i*0.1 + 0.05},{i*0.05},{i*0.12},{i%2}")
    eval_csv = "\n".join(eval_rows) + "\n"

    res_e = client.post(
        "/api/v1/datasets",
        data={"model_id": model_id, "dataset_type": "TEMPORAL_TRAJECTORY", "target_column": "Failure_Within_3"},
        files={"file": ("eval.csv", io.BytesIO(eval_csv.encode("utf-8")), "text/csv")},
    )
    assert res_e.status_code == 201
    eval_id = res_e.json()["dataset_id"]

    return {"model_id": model_id, "eval_id": eval_id}


def test_warning_unfitted_artifact_returns_not_available(setup_warning_resources):
    """Test that querying warning without a fitted artifact returns NOT_AVAILABLE (HTTP 200)."""
    res = setup_warning_resources
    response = client.post(
        "/api/v1/warnings",
        json={"model_id": res["model_id"], "evaluation_dataset_id": res["eval_id"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NOT_AVAILABLE"
    assert "not fitted" in data["reason"]
    assert data["horizon_unit"] == "controlled_degradation_states"


def test_warning_fitted_artifact_returns_available(setup_warning_resources):
    """Test that fitted Early Warning engine artifact executes warning query successfully."""
    res = setup_warning_resources

    import pandas as pd
    engine = EarlyWarningEngine(horizon_val=3)
    df_train = pd.DataFrame({
        "trajectory_id": [0, 0, 0, 0, 0],
        "step": [0, 1, 2, 3, 4],
        "ood_risk": [0.1, 0.4, 0.2, 0.8, 0.3],
        "uncertainty_risk": [0.1, 0.3, 0.2, 0.7, 0.2],
        "drift_risk": [0.0, 0.2, 0.1, 0.5, 0.1],
        "fused_risk": [0.1, 0.35, 0.2, 0.75, 0.25],
        "Failure_Within_3": [0, 1, 0, 1, 0],
    })
    df_val = df_train.copy()
    engine.fit(df_train, df_val, target_column="Failure_Within_3")

    artifact_dir = settings.ARTIFACTS_DIR / res["model_id"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(engine, artifact_dir / "warning_engine.joblib")

    response = client.post(
        "/api/v1/warnings",
        json={"model_id": res["model_id"], "evaluation_dataset_id": res["eval_id"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "AVAILABLE"
    assert data["horizon_unit"] == "controlled_degradation_states"
    assert data["is_warning_triggered"] is not None
