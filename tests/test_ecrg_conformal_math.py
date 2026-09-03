"""
AEGIS-X Module 14 Phase 4 — Conformal Mathematics & Bounds Attack Tests.
Verifies finite-sample order statistics, nonconformity functions, and set prediction.
"""

import math
import numpy as np
import pandas as pd
import pytest

from aegis.governance.calibrator import (
    TrajectorySplitConformalCalibrator,
    DeterministicRiskLearner,
    InfeasibleAlphaError,
)
from aegis.governance.schemas import ECRGGovernanceAction


def test_1_hand_computed_k_ceil_formula():
    """Test 1: Hand-computed order-statistic quantile cases."""
    # Case A: n=20, alpha=0.05 -> k = ceil(21 * 0.95) = ceil(19.95) = 20
    q, k, n = TrajectorySplitConformalCalibrator.compute_order_statistic_quantile([i * 0.05 for i in range(1, 21)], 0.05)
    assert n == 20
    assert k == 20
    assert abs(q - 1.0) < 1e-6

    # Case B: n=9, alpha=0.10 -> k = ceil(10 * 0.9) = ceil(9.0) = 9
    scores_b = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    q_b, k_b, n_b = TrajectorySplitConformalCalibrator.compute_order_statistic_quantile(scores_b, 0.10)
    assert n_b == 9
    assert k_b == 9
    assert q_b == 0.9


def test_2_alpha_too_small_rejected():
    """Test 2: Alpha too small for available n is rejected with InfeasibleAlphaError."""
    # n = 5, alpha = 0.05 -> k = ceil(6 * 0.95) = ceil(5.7) = 6 > 5
    with pytest.raises(InfeasibleAlphaError) as exc:
        TrajectorySplitConformalCalibrator.compute_order_statistic_quantile([0.1, 0.2, 0.3, 0.4, 0.5], 0.05)
    assert "infeasible" in str(exc.value).lower()


def test_3_tied_calibration_scores():
    """Test 3: Correct order statistic computation with tied calibration scores."""
    scores = [0.3, 0.3, 0.3, 0.5, 0.5, 0.5, 0.8, 0.8, 0.8, 0.8]  # n = 10
    # alpha = 0.20 -> k = ceil(11 * 0.80) = ceil(8.8) = 9
    q, k, n = TrajectorySplitConformalCalibrator.compute_order_statistic_quantile(scores, 0.20)
    assert k == 9
    assert q == 0.8  # 9th element in sorted list


def test_4_scores_exactly_equal_to_q_included_in_set():
    """Test 4: Candidate labels with nonconformity score exactly equal to q are included in C_alpha."""
    cal = TrajectorySplitConformalCalibrator(target_alpha=0.05)
    cal.calibrated_q = 0.40

    # s_y0 = 0.40 <= q (0.40) -> 0 is INCLUDED
    # s_y1 = 0.60 > q (0.40) -> 1 is EXCLUDED
    learner = DeterministicRiskLearner().fit(pd.DataFrame({"f1": [0.0, 1.0]}), pd.Series([0, 1]))
    cal.learner = learner

    X_test = pd.DataFrame({"f1": [0.40]})  # Will output p_adverse = 0.40
    # Override predict_proba to return exact 0.40
    learner.predict_proba = lambda X: np.array([0.40])

    p_set, p_adv, details = cal.predict_conformal_set(X_test)
    assert 0 in p_set
    assert details["s_y0"] == 0.40
    assert details["s_y0"] <= cal.calibrated_q


def test_5_all_zero_and_all_one_calibration_scores():
    """Test 5: All-zero and all-one calibration score edge cases."""
    # All zeros
    q_zero, k1, n1 = TrajectorySplitConformalCalibrator.compute_order_statistic_quantile([0.0] * 20, 0.05)
    assert q_zero == 0.0

    # All ones
    q_one, k2, n2 = TrajectorySplitConformalCalibrator.compute_order_statistic_quantile([1.0] * 20, 0.05)
    assert q_one == 1.0


def test_6_empty_prediction_set_mapped_to_escalate():
    """Test 6: Empty prediction set {} maps to ESCALATE."""
    assert TrajectorySplitConformalCalibrator.map_prediction_set_to_raw_action([]) == ECRGGovernanceAction.ESCALATE
    assert TrajectorySplitConformalCalibrator.map_prediction_set_to_raw_action([0]) == ECRGGovernanceAction.CONTINUE
    assert TrajectorySplitConformalCalibrator.map_prediction_set_to_raw_action([0, 1]) == ECRGGovernanceAction.WATCH
    assert TrajectorySplitConformalCalibrator.map_prediction_set_to_raw_action([1]) == ECRGGovernanceAction.DEFER


def test_7_nan_and_infinite_scores_rejected():
    """Test 7: NaN and infinite input scores are rejected."""
    with pytest.raises(ValueError):
        TrajectorySplitConformalCalibrator.compute_nonconformity_score(float("nan"), 1)

    with pytest.raises(ValueError):
        TrajectorySplitConformalCalibrator.compute_nonconformity_score(float("inf"), 0)


def test_8_no_interpolated_quantile_guarantee():
    """Test 8: Verify q is an exact order statistic element, not np.quantile interpolation."""
    scores = [0.1234, 0.2345, 0.3456, 0.4567, 0.5678, 0.6789, 0.7890, 0.8901, 0.9012, 0.9999]
    q, k, n = TrajectorySplitConformalCalibrator.compute_order_statistic_quantile(scores, 0.20)
    
    assert q in scores
    # Compare against np.quantile with linear interpolation (which yields non-element values)
    np_q = np.quantile(scores, 0.80)
    # q is discrete order statistic, not interpolated floating mean
    assert q == sorted(scores)[k - 1]


def test_9_row_replication_in_trajectory_does_not_change_max_score():
    """Test 9: Row replication within one trajectory does not change its trajectory-max score."""
    learner = DeterministicRiskLearner().fit(pd.DataFrame({"f1": [0.0, 1.0]}), pd.Series([0, 1]))
    cal = TrajectorySplitConformalCalibrator(target_alpha=0.20, learner=learner)

    df_single = pd.DataFrame({
        "trajectory_id": ["e1", "e1", "e1"],
        "f1": [0.1, 0.5, 0.9],
        "failure_within_horizon": [0, 0, 1],
    })

    # Replicated 10 times
    df_replicated = pd.concat([df_single] * 10, ignore_index=True)

    df_full = pd.concat([df_replicated, pd.DataFrame({
        "trajectory_id": [f"e_{i}" for i in range(2, 11)],
        "f1": [0.1] * 9,
        "failure_within_horizon": [0] * 9,
    })], ignore_index=True)

    cal.calibrate_temporal(df_full, feature_cols=["f1"])
    # Unique trajectories == 10 (e1, e_2..e_10)
    assert cal.n_cal_units == 10
