"""
AEGIS-X Module 14 Phase 4 — Artifact Security & Tamper Attack Tests.
Verifies safe JSON deserialization, SHA-256 hash checks, and finiteness validation.
"""

import json
import pandas as pd
import pytest

from aegis.governance.artifact import ECRGCalibratorArtifact, compare_deterministic_artifact_builds
from aegis.governance.calibrator import DeterministicRiskLearner, TrajectorySplitConformalCalibrator


@pytest.fixture
def valid_artifact_dict():
    """Constructs a valid artifact dictionary."""
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
    return art.to_dict()


def test_1_modified_payload_rejected_by_hash_mismatch(valid_artifact_dict):
    """Test 1: Modifying any value in JSON payload triggers SHA-256 mismatch rejection."""
    valid_artifact_dict["target_alpha"] = 0.01  # Tamper with target alpha
    with pytest.raises(ValueError) as exc:
        ECRGCalibratorArtifact.from_dict(valid_artifact_dict)
    assert "SHA-256 hash mismatch" in str(exc.value)


def test_2_modified_stored_hash_rejected(valid_artifact_dict):
    """Test 2: Modifying stored SHA-256 hash triggers rejection."""
    valid_artifact_dict["artifact_sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
    with pytest.raises(ValueError) as exc:
        ECRGCalibratorArtifact.from_dict(valid_artifact_dict)
    assert "SHA-256 hash mismatch" in str(exc.value)


def test_3_missing_required_key_rejected(valid_artifact_dict):
    """Test 3: Missing required key triggers rejection."""
    del valid_artifact_dict["calibrated_quantile"]
    with pytest.raises(ValueError) as exc:
        ECRGCalibratorArtifact.from_dict(valid_artifact_dict)
    assert "Missing required artifact key" in str(exc.value)


def test_4_unknown_schema_version_rejected(valid_artifact_dict):
    """Test 4: Unknown schema version is rejected."""
    valid_artifact_dict["artifact_schema_version"] = "99.0.0"
    with pytest.raises(ValueError) as exc:
        ECRGCalibratorArtifact.from_dict(valid_artifact_dict)
    assert "Incompatible artifact schema version" in str(exc.value) or "SHA-256 hash mismatch" in str(exc.value)


def test_5_nan_inf_parameters_rejected(valid_artifact_dict):
    """Test 5: NaN or infinite learner parameters trigger rejection."""
    valid_artifact_dict["learner_params"]["coef"] = [[float("nan")]]
    # Recompute hash so it passes hash check and hits finiteness check
    from aegis.governance.artifact import compute_canonical_hash
    valid_artifact_dict["artifact_sha256"] = compute_canonical_hash(valid_artifact_dict)

    with pytest.raises(ValueError) as exc:
        ECRGCalibratorArtifact.from_dict(valid_artifact_dict)
    assert "contains NaN or Infinity" in str(exc.value)


def test_6_zero_pickle_deserialization_in_artifact_path():
    """Test 6: Verify zero pickle imports or calls exist in artifact.py."""
    import aegis.governance.artifact as art_module
    import inspect

    source_code = inspect.getsource(art_module)
    assert "import pickle" not in source_code
    assert "pickle.loads" not in source_code
    assert "joblib" not in source_code


def test_7_two_equivalent_builds_produce_identical_scientific_hash(valid_artifact_dict):
    """Test 7: Two equivalent artifact builds produce identical canonical payload hash."""
    art1 = ECRGCalibratorArtifact.from_dict(valid_artifact_dict)
    art2 = ECRGCalibratorArtifact.from_dict(valid_artifact_dict)

    assert compare_deterministic_artifact_builds(art1, art2) is True
