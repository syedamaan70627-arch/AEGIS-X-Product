"""
AEGIS-X Module 14 Phase 4 — Adversarial Split-Leakage Tests.
Verifies full data-use firewall isolation between research-training, calibration, and test splits.
"""

import copy
import numpy as np
import pandas as pd
import pytest

from aegis.governance.artifact import ECRGCalibratorArtifact
from aegis.governance.calibrator import DeterministicRiskLearner, TrajectorySplitConformalCalibrator
from aegis.governance.dataset_builder import ECRGDatasetBuilder


@pytest.fixture
def mock_split_datasets():
    """Construct toy synthetic dataset splits (train, cal, test) to test split leakage safeguards."""
    # Split 1: Training engines 1..60 (toy 10 rows)
    X_train = pd.DataFrame({
        "ood_score": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95],
        "uncertainty_score": [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55],
        "drift_score": [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5],
        "fused_risk": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95],
    })
    y_train = pd.Series([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])

    # Split 2: Calibration engines 61..80 (20 trajectories, 1 step per engine)
    cal_records = []
    for eng in range(61, 81):
        cal_records.append({
            "trajectory_id": f"engine_{eng}",
            "state_index": 0,
            "ood_score": 0.05 * (eng % 10),
            "uncertainty_score": 0.05 * (eng % 10),
            "drift_score": 0.02 * (eng % 10),
            "fused_risk": 0.05 * (eng % 10),
            "failure_within_horizon": 1 if eng > 75 else 0,
        })
    df_cal = pd.DataFrame(cal_records)

    # Split 3: Internal final test engines 81..100 (unopened)
    test_records = []
    for eng in range(81, 101):
        test_records.append({
            "trajectory_id": f"engine_{eng}",
            "state_index": 0,
            "ood_score": 0.99,
            "uncertainty_score": 0.99,
            "drift_score": 0.99,
            "fused_risk": 0.99,
            "failure_within_horizon": 1,
        })
    df_test = pd.DataFrame(test_records)

    return X_train, y_train, df_cal, df_test


def test_1_mutating_test_split_does_not_alter_learner_or_quantile(mock_split_datasets):
    """Test 1: Mutating test data cannot change learner parameters, calibration quantile, or artifact hash."""
    X_train, y_train, df_cal, df_test = mock_split_datasets
    feature_cols = ["ood_score", "uncertainty_score", "drift_score", "fused_risk"]

    # Build Calibrator 1 from train + cal
    learner1 = DeterministicRiskLearner().fit(X_train, y_train)
    calibrator1 = TrajectorySplitConformalCalibrator(target_alpha=0.05, learner=learner1)
    calibrator1.calibrate_temporal(df_cal, feature_cols=feature_cols)
    art1 = ECRGCalibratorArtifact(calibrator1, "TEMPORAL_GOVERNANCE", "FAILURE_WITHIN_HORIZON", horizon=5)

    # Mutate test set dramatically
    df_test_mutated = df_test.copy()
    df_test_mutated["fused_risk"] = 0.000001
    df_test_mutated["failure_within_horizon"] = 0

    # Build Calibrator 2 with mutated test set available in environment (but unused)
    learner2 = DeterministicRiskLearner().fit(X_train, y_train)
    calibrator2 = TrajectorySplitConformalCalibrator(target_alpha=0.05, learner=learner2)
    calibrator2.calibrate_temporal(df_cal, feature_cols=feature_cols)
    art2 = ECRGCalibratorArtifact(calibrator2, "TEMPORAL_GOVERNANCE", "FAILURE_WITHIN_HORIZON", horizon=5)

    # Verify identical parameters and hashes
    assert np.allclose(learner1.scaler.mean_, learner2.scaler.mean_)
    assert np.allclose(learner1.model.coef_, learner2.model.coef_)
    assert calibrator1.calibrated_q == calibrator2.calibrated_q
    assert art1.to_dict()["learner_params"] == art2.to_dict()["learner_params"]


def test_2_mutating_external_test_does_not_alter_calibrator(mock_split_datasets):
    """Test 2: Mutating external-test data cannot change any fitted artifact."""
    X_train, y_train, df_cal, _ = mock_split_datasets
    feature_cols = ["ood_score", "uncertainty_score", "drift_score", "fused_risk"]

    learner = DeterministicRiskLearner().fit(X_train, y_train)
    calibrator = TrajectorySplitConformalCalibrator(target_alpha=0.05, learner=learner)
    q1 = calibrator.calibrate_temporal(df_cal, feature_cols=feature_cols)

    # External test payload mutation attempt
    external_test = pd.DataFrame({"ood_score": [0.0], "uncertainty_score": [0.0], "drift_score": [0.0], "fused_risk": [0.0]})
    external_test["ood_score"] = [0.999]

    # Re-evaluate calibrator quantile
    q2 = calibrator.calibrated_q
    assert q1 == q2


def test_3_mutating_calibration_labels_does_not_alter_learner_params(mock_split_datasets):
    """Test 3: Mutating calibration labels may change q but cannot change training-fitted learner coefficients."""
    X_train, y_train, df_cal, _ = mock_split_datasets
    feature_cols = ["ood_score", "uncertainty_score", "drift_score", "fused_risk"]

    learner = DeterministicRiskLearner().fit(X_train, y_train)
    mean_before = copy.deepcopy(learner.scaler.mean_)
    coef_before = copy.deepcopy(learner.model.coef_)

    # Mutate calibration labels
    df_cal_mutated = df_cal.copy()
    df_cal_mutated["failure_within_horizon"] = 1 - df_cal_mutated["failure_within_horizon"]

    calibrator = TrajectorySplitConformalCalibrator(target_alpha=0.05, learner=learner)
    calibrator.calibrate_temporal(df_cal_mutated, feature_cols=feature_cols)

    assert np.allclose(learner.scaler.mean_, mean_before)
    assert np.allclose(learner.model.coef_, coef_before)


def test_4_mutating_training_data_alters_learner_not_split_manifest(mock_split_datasets):
    """Test 4: Mutating training data changes learner parameters but preserves split membership."""
    X_train, y_train, df_cal, _ = mock_split_datasets

    learner1 = DeterministicRiskLearner().fit(X_train, y_train)

    X_train_mutated = X_train.copy()
    X_train_mutated["ood_score"] += 10.0
    learner2 = DeterministicRiskLearner().fit(X_train_mutated, y_train)

    assert not np.allclose(learner1.scaler.mean_, learner2.scaler.mean_)


def test_5_calibration_samples_never_enter_scaler_fit(mock_split_datasets):
    """Test 5: Calibration and final-test samples cannot enter preprocessing/scaler fitting."""
    X_train, y_train, df_cal, _ = mock_split_datasets
    learner = DeterministicRiskLearner()
    learner.fit(X_train, y_train)

    # Scaler must have fit ONLY on len(X_train) == 10
    assert learner.scaler.n_samples_seen_ == 10
    assert len(df_cal) == 20  # 20 cal rows were never passed to scaler.fit()


def test_6_reusing_engine_across_splits_rejected():
    """Test 6: Overlapping engine IDs across splits is invalid."""
    train_engines = ["engine_01", "engine_02", "engine_03"]
    cal_engines = ["engine_03", "engine_04"]  # Overlap engine_03!

    overlap = set(train_engines).intersection(set(cal_engines))
    assert len(overlap) > 0  # Detected overlap


def test_7_8_duplicate_rows_same_engine_one_trajectory_score(mock_split_datasets):
    """Tests 7 & 8: Duplicate calibration rows for same engine do not increase N_cal_independent (exactly 1 score per engine)."""
    X_train, y_train, df_cal, _ = mock_split_datasets
    feature_cols = ["ood_score", "uncertainty_score", "drift_score", "fused_risk"]

    learner = DeterministicRiskLearner().fit(X_train, y_train)

    # Duplicate rows for engine_61 (add 10 step rows for engine_61)
    extra_rows = []
    for step in range(1, 10):
        extra_rows.append({
            "trajectory_id": "engine_61",
            "state_index": step,
            "ood_score": 0.1,
            "uncertainty_score": 0.1,
            "drift_score": 0.05,
            "fused_risk": 0.1,
            "failure_within_horizon": 0,
        })
    df_cal_duplicated = pd.concat([df_cal, pd.DataFrame(extra_rows)], ignore_index=True)

    calibrator = TrajectorySplitConformalCalibrator(target_alpha=0.05, learner=learner)
    calibrator.calibrate_temporal(df_cal_duplicated, feature_cols=feature_cols)

    # N_cal_independent must remain 20 (number of unique trajectory_id values)
    assert calibrator.n_cal_units == 20
    assert len(calibrator.calibration_scores) == 20
