"""
AEGIS-X Module 14 — Reliability Governor & Artifact Unit Test Suite.
Tests Requirements 14-18, 26-27 from Section 12.
"""

import json
import pandas as pd
import pytest

from aegis.governance.artifact import ECRGCalibratorArtifact, compare_deterministic_artifact_builds
from aegis.governance.calibrator import DeterministicRiskLearner, TrajectorySplitConformalCalibrator
from aegis.governance.governor import ReliabilityGovernor
from aegis.governance.schemas import (
    ECRGEvidenceContract,
    ECRGOperatingMode,
    ECRGGovernanceAction,
    ECRGDecisionRecord,
)


@pytest.fixture
def sample_evidence():
    """Constructs clean sample evidence contract."""
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
    X_tr = df_cal[feature_cols]
    y_tr = df_cal["failure_within_horizon"]

    learner = DeterministicRiskLearner().fit(X_tr, y_tr)
    calibrator = TrajectorySplitConformalCalibrator(target_alpha=0.20, learner=learner)
    
    calibrator.calibrate_temporal(df_cal, trajectory_col="trajectory_id", target_col="failure_within_horizon", feature_cols=feature_cols)

    artifact = ECRGCalibratorArtifact(
        calibrator=calibrator,
        task_capability_profile="TEMPORAL_GOVERNANCE",
        target_semantic="FAILURE_WITHIN_HORIZON",
        horizon=5,
        training_dataset_hash="hash_train_123",
        calibration_dataset_hash="hash_cal_456",
        artifact_id="test_art_001",
    )
    return artifact


def test_14_explicit_evidence_only_behavior(sample_evidence):
    """Test 14: EVIDENCE_ONLY mode outputs calibrated=false and guarantee=null."""
    gov = ReliabilityGovernor(mode=ECRGOperatingMode.EVIDENCE_ONLY)
    record = gov.evaluate(sample_evidence)

    assert record.operating_mode == ECRGOperatingMode.EVIDENCE_ONLY
    assert record.calibrated is False
    assert record.guarantee_scope is None
    assert record.calibrator_artifact_id is None
    assert "EVIDENCE_ONLY_MODE_ACTIVE" in record.reason_codes


def test_15_no_silent_calibrated_mode_fallback(sample_evidence):
    """Test 15: Governor never silently downgrades to EVIDENCE_ONLY when CALIBRATED mode requested."""
    with pytest.raises(ValueError) as exc:
        ReliabilityGovernor(mode=ECRGOperatingMode.CALIBRATED_GOVERNANCE, artifact=None)
    assert "requires a validated ECRGCalibratorArtifact" in str(exc.value)

    gov = ReliabilityGovernor(mode=ECRGOperatingMode.EVIDENCE_ONLY)
    with pytest.raises(ValueError) as exc2:
        gov.evaluate(sample_evidence, requested_mode=ECRGOperatingMode.CALIBRATED_GOVERNANCE)
    assert "no calibrator artifact is loaded" in str(exc2.value)


def test_16_schema_feature_order_incompatibility_rejection(sample_evidence, calibrated_artifact):
    """Test 16: Feature order / schema mismatch rejection."""
    # Modify artifact learner feature names order
    calibrated_artifact.calibrator.learner.feature_names = ["wrong_f1", "wrong_f2"]
    
    gov = ReliabilityGovernor(artifact=calibrated_artifact, mode=ECRGOperatingMode.CALIBRATED_GOVERNANCE)
    with pytest.raises(ValueError) as exc:
        gov.evaluate(sample_evidence)
    assert any(phrase in str(exc.value) for phrase in ["Feature order", "feature names", "mismatch", "unseen", "missing", "NaN"])


def test_17_artifact_round_trip_determinism(calibrated_artifact):
    """Test 17: Artifact to_dict -> from_dict serialization preserves parameters."""
    d = calibrated_artifact.to_dict()
    reconstructed = ECRGCalibratorArtifact.from_dict(d)

    assert reconstructed.artifact_id == calibrated_artifact.artifact_id
    assert reconstructed.calibrator.target_alpha == calibrated_artifact.calibrator.target_alpha
    assert reconstructed.calibrator.calibrated_q == calibrated_artifact.calibrator.calibrated_q

    # Two-build comparison
    assert compare_deterministic_artifact_builds(calibrated_artifact, reconstructed) is True


def test_18_artifact_tamper_hash_rejection(calibrated_artifact):
    """Test 18: Rejects tampered or corrupted artifact payload hash."""
    d = calibrated_artifact.to_dict()
    
    # Tamper with calibrated quantile threshold
    d["calibrated_quantile"] = 0.001
    
    with pytest.raises(ValueError) as exc:
        ECRGCalibratorArtifact.from_dict(d)
    assert "SHA-256 hash mismatch" in str(exc.value) or "tampered" in str(exc.value)


def test_26_reason_code_and_audit_record_completeness(sample_evidence, calibrated_artifact):
    """Test 26: Audit record contains all Section 9 required fields."""
    gov = ReliabilityGovernor(artifact=calibrated_artifact, mode=ECRGOperatingMode.CALIBRATED_GOVERNANCE)
    record = gov.evaluate(sample_evidence)

    assert isinstance(record, ECRGDecisionRecord)
    assert record.decision_id is not None
    assert record.entity_id == "unit_001"
    assert record.state_index == 5
    assert record.operating_mode == ECRGOperatingMode.CALIBRATED_GOVERNANCE
    assert record.task_type == "TEMPORAL_GOVERNANCE"
    assert record.target_semantic == "FAILURE_WITHIN_HORIZON"
    assert record.horizon == 5
    assert record.unit == "controlled_degradation_states"
    assert record.alpha == 0.20
    assert 0.0 <= record.p_adverse <= 1.0
    assert "s_y0" in record.nonconformity_details
    assert "s_y1" in record.nonconformity_details
    assert isinstance(record.prediction_set, list)
    assert record.raw_action in [ECRGGovernanceAction.CONTINUE, ECRGGovernanceAction.WATCH, ECRGGovernanceAction.DEFER, ECRGGovernanceAction.ESCALATE]
    assert record.effective_action in [ECRGGovernanceAction.CONTINUE, ECRGGovernanceAction.WATCH, ECRGGovernanceAction.DEFER, ECRGGovernanceAction.ESCALATE]
    assert record.transition_reason is not None
    assert len(record.reason_codes) > 0
    assert record.evidence_snapshot_hash is not None
    assert record.calibrator_artifact_id == "test_art_001"
    assert record.calibrator_artifact_sha256 is not None
    assert record.schema_version == "1.0.0"
    assert record.calibration_unit_count == 10
    assert record.guarantee_scope is not None
    assert record.calibrated is True
    assert record.creation_timestamp is not None


def test_27_frozen_modules_1_13_regression_protection():
    """Test 27: Verify frozen modules imports remain unbroken."""
    from aegis.core.analyzer import CoreReliabilityAnalyzer
    from aegis.core.model_adapter import SklearnModelAdapter
    from aegis.fusion import StressRobustFusion
    from aegis.warning.engine import EarlyWarningEngine

    # Verify key frozen classes instantiate cleanly
    analyzer = CoreReliabilityAnalyzer()
    assert analyzer is not None
