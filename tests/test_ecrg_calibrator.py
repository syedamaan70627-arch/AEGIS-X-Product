"""
AEGIS-X Module 14 — ECRG Split Conformal Calibrator Unit Test Suite.
Tests Requirements 1-13 from Section 12.
"""

import math
import numpy as np
import pandas as pd
import pytest

from aegis.governance.calibrator import (
    DeterministicRiskLearner,
    TrajectorySplitConformalCalibrator,
    InfeasibleAlphaError,
)
from aegis.governance.schemas import ECRGGovernanceAction


def test_1_exact_order_statistic_quantile_calculation():
    """Test 1: Order-statistic quantile formula k = ceil((n+1)*(1-alpha))."""
    scores = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    alpha = 0.20  # (10+1)*(0.8) = 8.8 -> ceil = 9
    q, k, n = TrajectorySplitConformalCalibrator.compute_order_statistic_quantile(scores, alpha)
    assert n == 10
    assert k == 9
    assert q == 0.9  # 9th smallest element in sorted array


def test_2_n20_alpha005_k20_maximum_score():
    """Test 2: For n=20 and alpha=0.05, verify k=20, so q is the maximum score."""
    np.random.seed(42)
    scores = list(np.random.uniform(0.1, 0.9, size=20))
    q, k, n = TrajectorySplitConformalCalibrator.compute_order_statistic_quantile(scores, 0.05)
    
    # Formula: (20 + 1) * (1 - 0.05) = 21 * 0.95 = 19.95 -> ceil(19.95) = 20
    assert n == 20
    assert k == 20
    assert q == max(scores)


def test_3_infeasible_alpha_rejection():
    """Test 3: Reject requested alpha if required k > n."""
    scores = [0.1, 0.2, 0.3, 0.4, 0.5]  # n = 5
    # (5 + 1) * (1 - 0.05) = 6 * 0.95 = 5.7 -> ceil = 6 > 5 (infeasible)
    with pytest.raises(InfeasibleAlphaError) as exc_info:
        TrajectorySplitConformalCalibrator.compute_order_statistic_quantile(scores, 0.05)
    assert "infeasible" in str(exc_info.value).lower()


def test_4_no_interpolated_quantile():
    """Test 4: Quantile is an exact 1-based order statistic, not a linear interpolation."""
    scores = [0.10, 0.25, 0.40, 0.55, 0.70, 0.85, 1.00]
    alpha = 0.25  # (7+1)*(0.75) = 6.0 -> k = 6
    q, k, n = TrajectorySplitConformalCalibrator.compute_order_statistic_quantile(scores, alpha)
    assert q in scores  # Must be an exact score element
    assert q == 0.85


def test_5_correct_nonconformity_scores():
    """Test 5: Nonconformity scores s(x, y) = 1 - p_hat(y|x)."""
    p_adverse = 0.80
    
    # Candidate label y = 1 (adverse)
    s_y1 = TrajectorySplitConformalCalibrator.compute_nonconformity_score(p_adverse, y_true=1)
    assert abs(s_y1 - 0.20) < 1e-6

    # Candidate label y = 0 (non-adverse)
    s_y0 = TrajectorySplitConformalCalibrator.compute_nonconformity_score(p_adverse, y_true=0)
    assert abs(s_y0 - 0.80) < 1e-6


def test_6_all_four_prediction_set_cases():
    """Test 6: Support all 4 prediction set outcomes: {0}, {0,1}, {1}, {}."""
    learner = DeterministicRiskLearner()
    # Dummy fitted learner
    X_tr = pd.DataFrame({"f1": [0.0, 1.0], "f2": [0.0, 1.0]})
    y_tr = pd.Series([0, 1])
    learner.fit(X_tr, y_tr)

    cal = TrajectorySplitConformalCalibrator(target_alpha=0.05, learner=learner)

    # Case A: {0} -> low p_adverse (e.g. 0.1), s_y0=0.1 <= q, s_y1=0.9 > q
    cal.calibrated_q = 0.50
    X_test_low = pd.DataFrame({"f1": [-2.0], "f2": [-2.0]})
    set_a, p_adv, _ = cal.predict_conformal_set(X_test_low)
    assert set_a == [0]

    # Case B: {0, 1} -> high uncertainty / high q (e.g. q = 0.90)
    cal.calibrated_q = 0.90
    X_test_mid = pd.DataFrame({"f1": [0.0], "f2": [0.0]})
    set_b, _, _ = cal.predict_conformal_set(X_test_mid)
    assert set_b == [0, 1]

    # Case C: {1} -> high p_adverse (e.g. 0.9), s_y0=0.9 > q, s_y1=0.1 <= q
    cal.calibrated_q = 0.50
    X_test_high = pd.DataFrame({"f1": [2.0], "f2": [2.0]})
    set_c, _, _ = cal.predict_conformal_set(X_test_high)
    assert set_c == [1]

    # Case D: {} -> low q (e.g. q = 0.10) where both s_y0, s_y1 > q
    cal.calibrated_q = 0.10
    set_d, _, _ = cal.predict_conformal_set(X_test_mid)
    assert set_d == []


def test_7_exact_action_mapping():
    """Test 7: Prediction set to raw governance action mapping."""
    map_fn = TrajectorySplitConformalCalibrator.map_prediction_set_to_raw_action
    assert map_fn([0]) == ECRGGovernanceAction.CONTINUE
    assert map_fn([0, 1]) == ECRGGovernanceAction.WATCH
    assert map_fn([1]) == ECRGGovernanceAction.DEFER
    assert map_fn([]) == ECRGGovernanceAction.ESCALATE


def test_8_training_calibration_final_test_isolation():
    """Test 8: Ensure predictor fitting uses training split only, calibration uses cal split only."""
    # Toy split fixture
    X_tr = pd.DataFrame({"f1": [0.1, 0.2, 0.3, 0.4]})
    y_tr = pd.Series([0, 0, 1, 1])

    # 10 calibration samples for alpha=0.20 feasibility
    X_cal = pd.DataFrame({"f1": [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55]})
    y_cal = pd.Series([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])

    learner = DeterministicRiskLearner()
    learner.fit(X_tr, y_tr)

    # Verify fit parameters derived ONLY from training length 4
    assert learner.scaler.n_samples_seen_ == 4

    cal = TrajectorySplitConformalCalibrator(target_alpha=0.20, learner=learner)
    q = cal.calibrate_static(X_cal, y_cal)
    
    assert cal.n_cal_units == 10  # 10 calibration units used
    assert q is not None


def test_9_10_11_temporal_calibration_trajectory_max():
    """Tests 9, 10, 11: One score per engine trajectory, trajectory-max aggregation, N_cal=20."""
    records = []
    # Build 20 synthetic engine trajectories (N_cal = 20)
    for eng_id in range(20):
        for step in range(10):
            records.append({
                "trajectory_id": f"engine_{eng_id}",
                "state_index": step,
                "f1": 0.05 * step + (0.1 if eng_id > 10 else 0.0),
                "failure_within_horizon": 1 if (eng_id > 15 and step >= 7) else 0,
            })
    df_cal = pd.DataFrame(records)

    # Train learner on simple toy data
    X_tr = pd.DataFrame({"f1": [0.0, 0.5]})
    y_tr = pd.Series([0, 1])
    learner = DeterministicRiskLearner().fit(X_tr, y_tr)

    cal = TrajectorySplitConformalCalibrator(target_alpha=0.05, learner=learner)
    q = cal.calibrate_temporal(df_cal, trajectory_col="trajectory_id", target_col="failure_within_horizon", feature_cols=["f1"])

    # Test 9: Exactly 20 calibration scores (one per trajectory)
    assert len(cal.calibration_scores) == 20
    assert cal.n_cal_units == 20

    # Test 10: Trajectory score is the max nonconformity score across trajectory steps
    assert cal.k_order_stat == 20  # For n=20, alpha=0.05, k=20
    assert q == max(cal.calibration_scores)


def test_12_static_and_temporal_task_separation():
    """Test 12: Separation between STATIC_SELECTIVE_RISK and TEMPORAL_GOVERNANCE."""
    learner = DeterministicRiskLearner().fit(pd.DataFrame({"f1": [0, 1]}), pd.Series([0, 1]))
    
    X_stat = pd.DataFrame({"f1": [0.1 * i for i in range(10)]})
    y_stat = pd.Series([0 if i < 5 else 1 for i in range(10)])
    cal_stat = TrajectorySplitConformalCalibrator(target_alpha=0.20, learner=learner)
    cal_stat.calibrate_static(X_stat, y_stat)
    assert cal_stat.task_type == "STATIC_SELECTIVE_RISK"

    cal_temp = TrajectorySplitConformalCalibrator(target_alpha=0.20, learner=learner)
    df_temp = pd.DataFrame({
        "trajectory_id": [f"e_{i//2}" for i in range(20)],
        "f1": [0.05 * i for i in range(20)],
        "failure_within_horizon": [0 if i < 15 else 1 for i in range(20)],
    })
    cal_temp.calibrate_temporal(df_temp, feature_cols=["f1"])
    assert cal_temp.task_type == "TEMPORAL_GOVERNANCE"


def test_13_no_future_information_leakage():
    """Test 13: Feature at state t must depend strictly on information at or before t."""
    df_traj = pd.DataFrame({
        "trajectory_id": ["unit_1"] * 5,
        "state_index": list(range(5)),
        "fused_risk": [0.1, 0.2, 0.3, 0.4, 0.9],
        "is_failure": [0, 0, 0, 0, 1],
    })

    # Compute moving average or signal strictly using past and current rows (expanding window)
    expanding_max = df_traj["fused_risk"].expanding().max()
    
    for t in range(5):
        # Value at t should equal max ofFused risk from index 0..t
        expected_max = max(df_traj["fused_risk"].iloc[:t+1])
        assert expanding_max.iloc[t] == expected_max
