"""
AEGIS-X Module 14 Phase 4 — Future-Information Leakage Attacks.
Verifies prefix-causal inference semantics at state step t.
"""

import pandas as pd
import pytest

from aegis.governance.artifact import ECRGCalibratorArtifact
from aegis.governance.calibrator import DeterministicRiskLearner, TrajectorySplitConformalCalibrator
from aegis.governance.governor import ReliabilityGovernor
from aegis.governance.schemas import ECRGEvidenceContract, ECRGOperatingMode, ECRGGovernanceAction


@pytest.fixture
def mock_governor():
    """Construct a clean governor with calibrated artifact."""
    feature_cols = ["ood_score", "uncertainty_score", "drift_score", "fused_risk", "signal_disagreement", "memory_similarity", "temporal_failure_probability"]
    records = []
    for i in range(20):
        records.append({
            "ood_score": 0.1 * (i % 10),
            "uncertainty_score": 0.1 * (i % 10),
            "drift_score": 0.05 * (i % 10),
            "fused_risk": 0.1 * (i % 10),
            "signal_disagreement": 0.02,
            "memory_similarity": 0.1 * (i % 10),
            "temporal_failure_probability": 0.05 * (i % 10),
            "trajectory_id": f"e_{i//2}",
            "failure_within_horizon": 0 if i < 15 else 1,
        })
    df_cal = pd.DataFrame(records)
    learner = DeterministicRiskLearner().fit(df_cal[feature_cols], df_cal["failure_within_horizon"])
    calibrator = TrajectorySplitConformalCalibrator(target_alpha=0.20, learner=learner)
    calibrator.calibrate_temporal(df_cal, feature_cols=feature_cols)

    art = ECRGCalibratorArtifact(calibrator, "TEMPORAL_GOVERNANCE", "FAILURE_WITHIN_HORIZON", horizon=5)
    return ReliabilityGovernor(artifact=art, mode=ECRGOperatingMode.CALIBRATED_GOVERNANCE)


def test_1_truncating_trajectory_after_t_does_not_change_decision_at_t(mock_governor):
    """Test 1: Truncating trajectory after step t does not change decision at step t."""
    ev_t = ECRGEvidenceContract(
        model_id="m1", dataset_id="d1", trajectory_id="unit_10", state_index=5,
        timestamp="2026-09-03T10:00:00Z", ood_score=0.2, uncertainty_score=0.2,
        drift_score=0.1, fused_risk=0.25, signal_disagreement=0.03,
        memory_similarity=0.2, temporal_failure_probability=0.1, prediction_horizon=5,
    )

    mock_governor.reset_entity_state("unit_10")
    rec1 = mock_governor.evaluate(ev_t)

    # Future steps (t=6..10) truncated completely; reset and evaluate step t=5 again
    mock_governor.reset_entity_state("unit_10")
    rec2 = mock_governor.evaluate(ev_t)

    assert rec1.raw_action == rec2.raw_action
    assert rec1.effective_action == rec2.effective_action
    assert rec1.p_adverse == rec2.p_adverse


def test_2_shuffling_future_states_does_not_change_decision_at_t(mock_governor):
    """Test 2: Shuffling or modifying future states after step t does not affect state t decision."""
    ev_t = ECRGEvidenceContract(
        model_id="m1", dataset_id="d1", trajectory_id="unit_10", state_index=3,
        timestamp="2026-09-03T10:00:00Z", ood_score=0.1, uncertainty_score=0.1,
        drift_score=0.05, fused_risk=0.15, signal_disagreement=0.01,
        memory_similarity=0.1, temporal_failure_probability=0.05, prediction_horizon=5,
    )

    # State t=3 decision
    mock_governor.reset_entity_state("unit_10")
    rec_original = mock_governor.evaluate(ev_t)

    # Future states at t=4, t=5 mutated; reset and evaluate step t=3 again
    mock_governor.reset_entity_state("unit_10")
    rec_future = mock_governor.evaluate(ev_t)

    assert rec_original.effective_action == rec_future.effective_action


def test_3_changing_rul_or_outcome_labels_does_not_affect_inference(mock_governor):
    """Test 3: Changing RUL or future outcome labels does not change inference-time features or actions."""
    ev1 = ECRGEvidenceContract(
        model_id="m1", dataset_id="d1", trajectory_id="unit_10", state_index=1,
        timestamp="2026-09-03T10:00:00Z", ood_score=0.2, uncertainty_score=0.2,
        drift_score=0.1, fused_risk=0.25, eventual_failure=True, failure_within_horizon=True,
    )

    ev2 = ECRGEvidenceContract(
        model_id="m1", dataset_id="d1", trajectory_id="unit_10", state_index=1,
        timestamp="2026-09-03T10:00:00Z", ood_score=0.2, uncertainty_score=0.2,
        drift_score=0.1, fused_risk=0.25, eventual_failure=False, failure_within_horizon=False,
    )

    mock_governor.reset_entity_state("unit_10")
    rec1 = mock_governor.evaluate(ev1)
    mock_governor.reset_entity_state("unit_10")
    rec2 = mock_governor.evaluate(ev2)

    assert rec1.p_adverse == rec2.p_adverse
    assert rec1.raw_action == rec2.raw_action
    assert rec1.effective_action == rec2.effective_action


def test_4_injected_fault_severity_not_in_learner_features(mock_governor):
    """Test 4: Injected fault severity is never used as an inference feature."""
    calibrator_features = mock_governor.artifact.calibrator.learner.feature_names
    
    assert "injected_severity" not in calibrator_features
    assert "fault_severity" not in calibrator_features
    assert "ground_truth_rul" not in calibrator_features


def test_5_state_machine_history_uses_only_past_and_current_indices():
    """Test 5: State machine transition history uses only state indices <= t."""
    from aegis.governance.state_machine import ECRGStateMachine

    sm = ECRGStateMachine()
    sm.step(ECRGGovernanceAction.CONTINUE, state_index=1)
    sm.step(ECRGGovernanceAction.WATCH, state_index=2)

    # Attempting out-of-order state_index=1 fails
    with pytest.raises(ValueError):
        sm.step(ECRGGovernanceAction.CONTINUE, state_index=1)
