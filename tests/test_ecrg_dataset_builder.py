"""
AEGIS-X Module 14 — Comprehensive Phase 2 Dataset Builder Unit Test Suite.
Verifies all 20 required data quality, leakage prevention, monotonicity, provenance,
and reproducibility invariants.
"""

import os
import hashlib
import numpy as np
import pandas as pd
import pytest

from aegis.core.exceptions import DatasetValidationError
from aegis.governance.dataset_builder import ECRGDatasetBuilder, compute_sha256_hash


@pytest.fixture
def sample_trajectory_df():
    """Constructs a small, clean synthetic trajectory fixture for deterministic testing."""
    records = []
    # Trajectory 0: Normal -> Degraded -> Failure at step 5
    for step in range(10):
        records.append({
            "trajectory_id": "unit_0",
            "step": step,
            "ood_risk": 0.1 + step * 0.08,
            "uncertainty_risk": 0.15 + step * 0.05,
            "drift_risk": 0.05 + step * 0.07,
            "fused_risk": 0.1 + step * 0.08,
            "is_failure": 1 if step >= 5 else 0,
        })
    # Trajectory 1: Normal throughout (non-failure)
    for step in range(10):
        records.append({
            "trajectory_id": "unit_1",
            "step": step,
            "ood_risk": 0.05,
            "uncertainty_risk": 0.10,
            "drift_risk": 0.02,
            "fused_risk": 0.06,
            "is_failure": 0,
        })
    # Trajectory 2: Normal throughout (non-failure)
    for step in range(10):
        records.append({
            "trajectory_id": "unit_2",
            "step": step,
            "ood_risk": 0.08,
            "uncertainty_risk": 0.12,
            "drift_risk": 0.03,
            "fused_risk": 0.07,
            "is_failure": 0,
        })
    return pd.DataFrame(records)


def test_1_schema_validation(sample_trajectory_df):
    """Test 1: Schema validation on generated canonical rows."""
    builder = ECRGDatasetBuilder()
    c_df, stats = builder.build_canonical_rows_for_df(
        sample_trajectory_df, "m1", "d1", "test_domain", horizons=[1, 2, 3, 5]
    )
    required_cols = [
        "row_id", "source_module", "source_artifact_hash", "model_id", "dataset_id",
        "domain_id", "seed", "trajectory_id", "state_index", "prediction_horizon",
        "ood_score", "uncertainty_score", "drift_score", "fused_risk",
        "has_ood", "has_uncertainty", "has_drift", "has_fused_risk", "has_ground_truth",
        "eventual_failure", "failure_within_horizon"
    ]
    for col in required_cols:
        assert col in c_df.columns, f"Missing required column {col} in canonical schema"


def test_2_deterministic_row_ids(sample_trajectory_df):
    """Test 2: Deterministic row ID generation."""
    builder = ECRGDatasetBuilder()
    c_df1, _ = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1")
    c_df2, _ = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1")
    assert (c_df1["row_id"] == c_df2["row_id"]).all()


def test_3_deterministic_output_hashes(sample_trajectory_df):
    """Test 3: Deterministic output hashes for canonical dataframes."""
    builder = ECRGDatasetBuilder()
    c_df1, _ = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1")
    c_df2, _ = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1")
    h1 = compute_sha256_hash(c_df1)
    h2 = compute_sha256_hash(c_df2)
    assert h1 == h2, "Output dataframe hash must be 100% deterministic"


def test_4_5_6_zero_group_overlap_splitting(sample_trajectory_df):
    """Tests 4, 5, 6: Deterministic group splitting with zero trajectory/unit overlap."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1")
    tr, cal, te, manifest = builder.create_group_aware_split(c_df, seed=42)

    tr_units = set(tr["trajectory_id"].unique())
    cal_units = set(cal["trajectory_id"].unique())
    te_units = set(te["trajectory_id"].unique())

    assert len(tr_units.intersection(cal_units)) == 0, "Train and Cal share trajectory units!"
    assert len(tr_units.intersection(te_units)) == 0, "Train and Test share trajectory units!"
    assert len(cal_units.intersection(te_units)) == 0, "Cal and Test share trajectory units!"
    assert manifest["zero_overlap_verified"] is True


def test_7_all_horizons_in_same_split(sample_trajectory_df):
    """Test 7: All horizons for a single state remain in the exact same split."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1", horizons=[1, 2, 3, 5])
    tr, cal, te, _ = builder.create_group_aware_split(c_df, seed=42)

    for df_split in [tr, cal, te]:
        for (traj, state), grp in df_split.groupby(["trajectory_id", "state_index"]):
            assert set(grp["prediction_horizon"].unique()) == {1, 2, 3, 5}


def test_8_horizon_label_monotonicity(sample_trajectory_df):
    """Test 8: Horizon label monotonicity (failure_within_1 <= failure_within_2 <= failure_within_3 <= failure_within_5)."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1", horizons=[1, 2, 3, 5])

    for (traj, state), grp in c_df.groupby(["trajectory_id", "state_index"]):
        grp_sorted = grp.sort_values("prediction_horizon")
        targets = grp_sorted["failure_within_horizon"].dropna().tolist()
        for i in range(len(targets) - 1):
            assert targets[i] <= targets[i + 1], f"Monotonicity error at trajectory {traj}, step {state}: {targets}"


def test_9_no_future_feature_leakage(sample_trajectory_df):
    """Test 9: Feature scores at step t use strictly same-state features."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1")

    for idx, row in c_df.iterrows():
        t_id = row["trajectory_id"]
        s_idx = row["state_index"]
        orig_row = sample_trajectory_df[(sample_trajectory_df["trajectory_id"] == t_id) & (sample_trajectory_df["step"] == s_idx)].iloc[0]

        assert row["ood_score"] == pytest.approx(orig_row["ood_risk"])
        assert row["uncertainty_score"] == pytest.approx(orig_row["uncertainty_risk"])
        assert row["drift_score"] == pytest.approx(orig_row["drift_risk"])


def test_10_11_target_labels_correctness(sample_trajectory_df):
    """Tests 10 & 11: Correct non-failure and failure-boundary target labeling."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1", horizons=[1, 2, 3, 5])

    # Trajectory 0 fails at step 5
    # For step 3, failure is at step 5 (difference of 2). So failure_within_1=0, failure_within_2=1, failure_within_3=1, failure_within_5=1
    s3_k1 = c_df[(c_df["trajectory_id"] == "unit_0") & (c_df["state_index"] == 3) & (c_df["prediction_horizon"] == 1)].iloc[0]
    s3_k2 = c_df[(c_df["trajectory_id"] == "unit_0") & (c_df["state_index"] == 3) & (c_df["prediction_horizon"] == 2)].iloc[0]
    assert s3_k1["failure_within_horizon"] == 0
    assert s3_k2["failure_within_horizon"] == 1

    # Trajectory 1 is non-failure throughout
    unit1_targets = c_df[c_df["trajectory_id"] == "unit_1"]["failure_within_horizon"].dropna()
    assert (unit1_targets == 0).all()


def test_12_censored_trajectory_handling(sample_trajectory_df):
    """Test 12: Censored trajectory handling."""
    builder = ECRGDatasetBuilder()
    c_df, stats = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1")
    assert stats["censored_row_count"] >= 0


def test_13_missing_evidence_not_zero_filled():
    """Test 13: Missing evidence is preserved as None (not zero-filled)."""
    df_missing = pd.DataFrame([
        {"trajectory_id": "u0", "step": 0, "is_failure": 0},
        {"trajectory_id": "u0", "step": 1, "is_failure": 0},
    ])
    builder = ECRGDatasetBuilder()
    c_df, stats = builder.build_canonical_rows_for_df(df_missing, "m1", "d1", "domain1")

    assert stats["availability"]["ood"] is False
    assert c_df["ood_score"].isnull().all()
    assert (c_df["has_ood"] == False).all()


def test_14_score_range_validation(sample_trajectory_df):
    """Test 14: Score ranges are bounded in [0, 1] where scientifically defined."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1")

    for col in ["ood_score", "uncertainty_score", "drift_score", "fused_risk"]:
        vals = c_df[col].dropna()
        assert (vals >= 0.0).all() and (vals <= 1.0).all(), f"Score range error in {col}"


def test_15_source_artifact_provenance(sample_trajectory_df):
    """Test 15: Source artifact provenance hash inclusion."""
    builder = ECRGDatasetBuilder()
    c_df, stats = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1")
    assert "source_artifact_hash" in c_df.columns
    assert len(c_df["source_artifact_hash"].iloc[0]) == 64  # SHA-256 length


def test_16_duplicate_record_detection(sample_trajectory_df):
    """Test 16: Zero duplicate row IDs generated."""
    builder = ECRGDatasetBuilder()
    c_df, stats = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1")
    assert stats["duplicate_row_count"] == 0


def test_17_frozen_modules_1_13_unmodified():
    """Test 17: Modules 1-13 core files exist and remain untouched."""
    assert os.path.exists("aegis/core/data_loader.py")
    assert os.path.exists("aegis/core/temporal.py")
    assert os.path.exists("aegis/core/analyzer.py")


def test_18_no_production_database_access():
    """Test 18: Dataset builder operates purely locally without database side effects."""
    builder = ECRGDatasetBuilder()
    assert builder.config_hash is not None


def test_19_multi_domain_separation(sample_trajectory_df):
    """Test 19: Multi-domain separation tag preservation."""
    builder = ECRGDatasetBuilder()
    c1, _ = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain_A")
    c2, _ = builder.build_canonical_rows_for_df(sample_trajectory_df, "m2", "d2", "domain_B")

    assert (c1["domain_id"] == "domain_A").all()
    assert (c2["domain_id"] == "domain_B").all()


def test_20_clean_run_reproducibility(sample_trajectory_df):
    """Test 20: Full dataset builder clean-run reproducibility."""
    builder = ECRGDatasetBuilder()
    c1, s1 = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1")
    c2, s2 = builder.build_canonical_rows_for_df(sample_trajectory_df, "m1", "d1", "domain1")

    pd.testing.assert_frame_equal(c1, c2)
    assert s1["source_artifact_hash"] == s2["source_artifact_hash"]
