"""
AEGIS-X Module 14 Phase 4 — Decision Record Audit & Privacy Tests.
Verifies completeness of audit trail and absence of sensitive payload exposure.
"""

import json
import pandas as pd
import pytest

from aegis.governance.artifact import ECRGCalibratorArtifact
from aegis.governance.calibrator import DeterministicRiskLearner, TrajectorySplitConformalCalibrator
from aegis.governance.governor import ReliabilityGovernor
from aegis.governance.schemas import ECRGEvidenceContract, ECRGOperatingMode, ECRGDecisionRecord


@pytest.fixture
def governor_and_evidence():
    """Construct governor and clean evidence."""
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

    art = ECRGCalibratorArtifact(calibrator, "TEMPORAL_GOVERNANCE", "FAILURE_WITHIN_HORIZON", horizon=5)
    gov = ReliabilityGovernor(artifact=art, mode=ECRGOperatingMode.CALIBRATED_GOVERNANCE)

    ev = ECRGEvidenceContract(
        model_id="m1", dataset_id="d1", trajectory_id="u1", state_index=0,
        timestamp="2026-09-03T10:00:00Z", ood_score=0.1, uncertainty_score=0.1,
        drift_score=0.05, fused_risk=0.1,
    )
    return gov, ev


def test_1_decision_record_field_completeness(governor_and_evidence):
    """Test 1: Decision record contains all Section 9 required fields."""
    gov, ev = governor_and_evidence
    record = gov.evaluate(ev)

    assert isinstance(record, ECRGDecisionRecord)
    assert record.decision_id.startswith("dec-")
    assert record.entity_id == "u1"
    assert record.state_index == 0
    assert record.task_type == "TEMPORAL_GOVERNANCE"
    assert record.dataset_profile == "TEMPORAL_GOVERNANCE"
    assert record.operating_mode == ECRGOperatingMode.CALIBRATED_GOVERNANCE
    assert record.target_semantic == "FAILURE_WITHIN_HORIZON"
    assert record.horizon == 5
    assert record.unit == "controlled_degradation_states"
    assert record.alpha == 0.20
    assert 0.0 <= record.p_adverse <= 1.0
    assert "quantile_q" in record.nonconformity_details
    assert isinstance(record.prediction_set, list)
    assert record.raw_action is not None
    assert record.effective_action is not None
    assert record.transition_reason is not None
    assert isinstance(record.reason_codes, list)
    assert len(record.evidence_snapshot_hash) == 64  # SHA-256 hash length
    assert record.calibrator_artifact_id is not None
    assert len(record.calibrator_artifact_sha256) == 64
    assert record.schema_version == "1.0.0"
    assert record.calibration_unit_count == 10
    assert record.guarantee_scope is not None
    assert record.calibrated is True
    assert record.creation_timestamp is not None


def test_2_no_sensitive_data_exposure(governor_and_evidence):
    """Test 2: Zero raw datasets, authentication tokens, Supabase secrets, or binary weights in record JSON."""
    gov, ev = governor_and_evidence
    record = gov.evaluate(ev)
    record_json = record.model_dump_json()

    forbidden_tokens = ["sb_secret", "bearer", "password", "raw_dataset", "coef_", "intercept_"]
    for token in forbidden_tokens:
        assert token not in record_json.lower()


def test_3_evidence_snapshot_hash_is_canonical_sha256(governor_and_evidence):
    """Test 3: Evidence snapshot hash is deterministic SHA-256 digest of input contract."""
    gov, ev = governor_and_evidence
    gov.reset_entity_state("u1")
    record1 = gov.evaluate(ev)
    gov.reset_entity_state("u1")
    record2 = gov.evaluate(ev)

    assert record1.evidence_snapshot_hash == record2.evidence_snapshot_hash
