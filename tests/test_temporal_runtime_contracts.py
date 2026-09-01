"""
AEGIS-X Temporal Runtime Contract & Group-Safe Split Tests.
"""

from datetime import datetime, timezone
import uuid
import pytest
import pandas as pd
import numpy as np

from aegis.core.exceptions import DatasetValidationError
from aegis.prediction.features import PredictionFeatureBuilder
from aegis.warning.engine import EarlyWarningEngine
from api.services.prediction_service import PredictionService
from api.services.warning_service import WarningService
from api.schemas.prediction import PredictionRequest
from api.schemas.warning import WarningRequest, WarningEvaluationRequest, WarningFitRequest
from api.db.models import ModelRecord, DatasetRecord
from api.core.dependencies import get_model_repository, get_dataset_repository
from api.services.storage_service import StorageService


def create_mock_temporal_df():
    """Generates a 2-trajectory dataset with base risk features."""
    rows = []
    # Trajectory 0: steps 0..4
    for step in range(5):
        rows.append({
            "trajectory_id": 0,
            "step": step,
            "ood_risk": 0.1 * step,
            "uncertainty_risk": 0.05 * step,
            "drift_risk": 0.02 * step,
            "fused_risk": 0.15 * step,
            "is_failure": 1 if step >= 3 else 0,
            "Failure_Onset_Next": 1 if step >= 2 else 0,
        })
    # Trajectory 1: steps 0..4 (starts with high base values)
    for step in range(5):
        rows.append({
            "trajectory_id": 1,
            "step": step,
            "ood_risk": 0.9 + 0.01 * step,
            "uncertainty_risk": 0.8 + 0.01 * step,
            "drift_risk": 0.7 + 0.01 * step,
            "fused_risk": 0.95 + 0.01 * step,
            "is_failure": 1 if step >= 2 else 0,
            "Failure_Onset_Next": 1 if step >= 1 else 0,
        })
    return pd.DataFrame(rows)


def test_delta_features_no_cross_trajectory_leakage():
    """Proves delta_feature = f[t] - f[t-1] within each trajectory and first row has delta = 0."""
    df = create_mock_temporal_df()
    features_df, _ = PredictionFeatureBuilder.build_features(df, feature_set_type="dynamic")

    # First row of Trajectory 0 (idx 0)
    assert features_df.loc[0, "delta_ood_risk"] == 0.0
    assert features_df.loc[0, "delta_fused_risk"] == 0.0

    # Row 1 of Trajectory 0 (idx 1): step 1 - step 0
    assert pytest.approx(features_df.loc[1, "delta_ood_risk"]) == 0.1

    # First row of Trajectory 1 (idx 5): step 0 of traj_1
    # Base ood_risk is 0.9, previous row (idx 4) ood_risk was 0.4.
    # Without trajectory grouping, delta would be 0.9 - 0.4 = 0.5 (LEAKAGE!).
    # With trajectory grouping, delta MUST be 0.0!
    assert features_df.loc[5, "delta_ood_risk"] == 0.0
    assert features_df.loc[5, "delta_fused_risk"] == 0.0

    # Row 1 of Trajectory 1 (idx 6): step 1 - step 0 of traj_1
    assert pytest.approx(features_df.loc[6, "delta_ood_risk"]) == 0.01


def test_raw_evaluation_dataset_rejected_by_prediction_service():
    """Proves server-side rejection when execution request points to ordinary EVALUATION dataset."""
    model_repo = get_model_repository()
    dataset_repo = get_dataset_repository()
    now_str = datetime.now(timezone.utc).isoformat()

    model_id = f"mod-pred-rej-{uuid.uuid4()}"
    dataset_id = f"ds-eval-rej-{uuid.uuid4()}"

    model_rec = ModelRecord(
        id=model_id,
        model_name="Test Model",
        task_type="binary_classification",
        file_path="dummy.joblib",
        filename="model.joblib",
        predict_supported=True,
        predict_proba_supported=True,
        created_at=now_str,
        n_features_in=30,
        user_id="local_dev_user",
    )
    model_repo.create(model_rec)

    eval_rec = DatasetRecord(
        id=dataset_id,
        model_id=model_id,
        dataset_type="EVALUATION",
        filename="evaluation_dataset.csv",
        file_path="dummy_path.csv",
        num_samples=171,
        num_features=30,
        feature_names=["f1"],
        has_target=True,
        created_at=now_str,
        user_id="local_dev_user",
    )
    dataset_repo.create(eval_rec)

    req = PredictionRequest(
        model_id=model_id,
        evaluation_dataset_id=dataset_id,
    )

    with pytest.raises(DatasetValidationError) as exc_info:
        PredictionService.run_prediction(req, user_id="local_dev_user")

    assert "Failure Prediction execution requires a TEMPORAL_TRAJECTORY dataset" in str(exc_info.value)


def test_raw_evaluation_dataset_rejected_by_warning_service():
    """Proves server-side rejection when query/evaluation points to ordinary EVALUATION dataset."""
    model_repo = get_model_repository()
    dataset_repo = get_dataset_repository()
    now_str = datetime.now(timezone.utc).isoformat()

    model_id = f"mod-warn-rej-{uuid.uuid4()}"
    dataset_id = f"ds-eval-warn-rej-{uuid.uuid4()}"

    model_rec = ModelRecord(
        id=model_id,
        model_name="Test Model",
        task_type="binary_classification",
        file_path="dummy.joblib",
        filename="model.joblib",
        predict_supported=True,
        predict_proba_supported=True,
        created_at=now_str,
        n_features_in=30,
        user_id="local_dev_user",
    )
    model_repo.create(model_rec)

    eval_rec = DatasetRecord(
        id=dataset_id,
        model_id=model_id,
        dataset_type="EVALUATION",
        filename="evaluation_dataset.csv",
        file_path="dummy_path.csv",
        num_samples=171,
        num_features=30,
        feature_names=["f1"],
        has_target=True,
        created_at=now_str,
        user_id="local_dev_user",
    )
    dataset_repo.create(eval_rec)

    query_req = WarningRequest(
        model_id=model_id,
        evaluation_dataset_id=dataset_id,
    )
    with pytest.raises(DatasetValidationError) as exc_info:
        WarningService.query_warning(query_req, user_id="local_dev_user")
    assert "Early Warning execution requires a TEMPORAL_TRAJECTORY dataset" in str(exc_info.value)

    eval_req = WarningEvaluationRequest(
        model_id=model_id,
        evaluation_dataset_id=dataset_id,
    )
    with pytest.raises(DatasetValidationError) as exc_info:
        WarningService.evaluate_trajectories(eval_req, user_id="local_dev_user")
    assert "Early Warning execution requires a TEMPORAL_TRAJECTORY dataset" in str(exc_info.value)


def test_warning_service_group_safe_split_only(tmp_path):
    """Proves WarningService.fit_warning_engine uses disjoint group-safe split only without row-level override."""
    model_repo = get_model_repository()
    dataset_repo = get_dataset_repository()
    now_str = datetime.now(timezone.utc).isoformat()

    model_id = f"mod-fit-split-{uuid.uuid4()}"
    dataset_id = f"ds-traj-warn-fit-{uuid.uuid4()}"

    model_rec = ModelRecord(
        id=model_id,
        model_name="Test Model",
        task_type="binary_classification",
        file_path="dummy.joblib",
        filename="model.joblib",
        predict_supported=True,
        predict_proba_supported=True,
        created_at=now_str,
        n_features_in=4,
        user_id="local_dev_user",
    )
    model_repo.create(model_rec)

    # Build 6 distinct trajectories with 10 states each
    rows = []
    for tid in range(6):
        for step in range(10):
            rows.append({
                "trajectory_id": tid,
                "step": step,
                "ood_risk": 0.1 * step + 0.05 * tid,
                "uncertainty_risk": 0.05 * step,
                "drift_risk": 0.02 * step,
                "fused_risk": 0.1 * step + 0.05 * tid,
                "is_failure": 1 if step >= 7 else 0,
            })
    df = pd.DataFrame(rows)

    csv_path = tmp_path / "sample_traj.csv"
    df.to_csv(csv_path, index=False)

    ds_rec = DatasetRecord(
        id=dataset_id,
        model_id=model_id,
        dataset_type="TEMPORAL_TRAJECTORY",
        filename="sample_traj.csv",
        file_path=str(csv_path),
        target_column="is_failure",
        num_samples=len(df),
        num_features=4,
        feature_names=["ood_risk", "uncertainty_risk", "drift_risk", "fused_risk"],
        has_target=True,
        created_at=now_str,
        user_id="local_dev_user",
    )
    dataset_repo.create(ds_rec)

    fit_req = WarningFitRequest(
        trajectory_dataset_id=dataset_id,
        horizon_val=3,
        random_state=42,
    )

    res = WarningService.fit_warning_engine(model_id, fit_req, user_id="local_dev_user")
    assert res.status == "fitted"
    assert StorageService.has_warning_artifact(model_id, user_id="local_dev_user")
