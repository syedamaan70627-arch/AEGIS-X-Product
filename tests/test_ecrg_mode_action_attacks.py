"""
AEGIS-X Module 14 Phase 4 — Operating Mode & Action Attack Tests.
Verifies mode safety boundaries, fallback prevention, and action completeness.
"""

import pandas as pd
import pytest

from aegis.governance.artifact import ECRGCalibratorArtifact
from aegis.governance.calibrator import DeterministicRiskLearner, TrajectorySplitConformalCalibrator
from aegis.governance.governor import ReliabilityGovernor
from aegis.governance.schemas import ECRGEvidenceContract, ECRGOperatingMode, ECRGGovernanceAction


@pytest.fixture
def clean_evidence():
    """Constructs clean evidence contract."""
    return ECRGEvidenceContract(
        model_id="test_model_v1",
        dataset_id="cmapss_fd001",
        trajectory_id="unit_001",
        state_index=5,
        timestamp="2026-09-03T10:00:00Z",
        ood_score=0.15,
        uncertainty_score=0.20,
        drift_score=0.10,
        fused_risk=0.25,
        signal_disagreement=0.05,
        memory_similarity=0.30,
        temporal_failure_probability=0.15,
        early_warning_state="NORMAL",
        prediction_horizon=5,
    )


@pytest.fixture
def calibrated_artifact():
    """Constructs a clean, fitted calibrator artifact for testing."""
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
    feature_cols = ["ood_score", "uncertainty_score", "drift_score", "fused_risk", "signal_disagreement", "memory_similarity", "temporal_failure_probability"]
    
    learner = DeterministicRiskLearner().fit(df_cal[feature_cols], df_cal["failure_within_horizon"])
    calibrator = TrajectorySplitConformalCalibrator(target_alpha=0.20, learner=learner)
    calibrator.calibrate_temporal(df_cal, trajectory_col="trajectory_id", target_col="failure_within_horizon", feature_cols=feature_cols)

    return ECRGCalibratorArtifact(calibrator, "TEMPORAL_GOVERNANCE", "FAILURE_WITHIN_HORIZON", horizon=5)


def test_1_calibrated_mode_without_artifact_fails_closed(clean_evidence):
    """Test 1: Calibrated mode without an artifact fails closed (raises ValueError)."""
    with pytest.raises(ValueError) as exc:
        ReliabilityGovernor(mode=ECRGOperatingMode.CALIBRATED_GOVERNANCE, artifact=None)
    assert "requires a validated ECRGCalibratorArtifact" in str(exc.value)


def test_2_no_silent_fallback_to_evidence_only(clean_evidence):
    """Test 2: Calibrated mode never silently downgrades to EVIDENCE_ONLY."""
    gov = ReliabilityGovernor(mode=ECRGOperatingMode.EVIDENCE_ONLY)
    with pytest.raises(ValueError) as exc:
        gov.evaluate(clean_evidence, requested_mode=ECRGOperatingMode.CALIBRATED_GOVERNANCE)
    assert "no calibrator artifact is loaded" in str(exc.value)


def test_3_evidence_only_output_attributes(clean_evidence):
    """Test 3: Evidence-only output always has calibrated=false and guarantee=null."""
    gov = ReliabilityGovernor(mode=ECRGOperatingMode.EVIDENCE_ONLY)
    record = gov.evaluate(clean_evidence)

    assert record.calibrated is False
    assert record.guarantee_scope is None
    assert record.operating_mode == ECRGOperatingMode.EVIDENCE_ONLY
    assert "EVIDENCE_ONLY_MODE_ACTIVE" in record.reason_codes


def test_4_calibrated_output_contains_complete_conformal_telemetry(clean_evidence, calibrated_artifact):
    """Test 4: Calibrated output includes alpha, n, k, q, artifact hash, and guarantee scope."""
    gov = ReliabilityGovernor(artifact=calibrated_artifact, mode=ECRGOperatingMode.CALIBRATED_GOVERNANCE)
    record = gov.evaluate(clean_evidence)

    assert record.calibrated is True
    assert record.alpha == 0.20
    assert record.calibration_unit_count == 10
    assert "quantile_q" in record.nonconformity_details
    assert record.calibrator_artifact_sha256 is not None
    assert record.guarantee_scope is not None
    assert "Marginal finite-sample split-conformal" in record.guarantee_scope


def test_5_invalid_or_corrupted_evidence_returns_escalate():
    """Test 5: Invalid or corrupted evidence (NaN/Inf) returns safe ESCALATE."""
    corrupted_ev = ECRGEvidenceContract.model_construct(
        model_id="m1", dataset_id="d1", trajectory_id="u1", state_index=0,
        timestamp="2026-09-03T10:00:00Z", ood_score=float("nan"), uncertainty_score=0.1,
        drift_score=0.1, fused_risk=0.1, signal_disagreement=0.0, memory_similarity=0.0,
        temporal_failure_probability=0.0, early_warning_state="NORMAL", prediction_horizon=5,
    )
    gov = ReliabilityGovernor(mode=ECRGOperatingMode.EVIDENCE_ONLY)
    record = gov.evaluate(corrupted_ev)

    assert record.effective_action == ECRGGovernanceAction.ESCALATE
    assert "CRITICAL_EVIDENCE_CORRUPTED" in record.reason_codes
