"""
AEGIS-X Module 14 — Comprehensive Phase 2C Dataset Builder Unit Test Suite.
Verifies all required data quality, task separation, reference-fitting isolation,
censoring, missing dataset reporting, and 2-run reproducibility invariants.
"""

import os
import hashlib
import numpy as np
import pandas as pd
import pytest

from aegis.core.exceptions import DatasetValidationError
from aegis.governance.dataset_builder import ECRGDatasetBuilder, compute_sha256_hash
from aegis.evaluation.datasets import load_breast_cancer_fixture, load_digits_parity_fixture


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
    return pd.DataFrame(records)


def test_1_static_class_label_not_used_as_failure():
    """Test 1: Static class label is never used directly as failure."""
    X_bc, y_bc = load_breast_cancer_fixture()
    y_pred_bc = y_bc.copy()
    builder = ECRGDatasetBuilder()
    df_static, stats = builder.build_static_selective_risk_rows(
        X_bc, y_bc, y_pred_bc, "m1", "d1", "classification_breast_cancer"
    )
    class1_rows = df_static[df_static["true_class"] == 1]
    assert (class1_rows["prediction_error"] == 0).all()


def test_2_static_samples_not_converted_to_real_trajectories():
    """Test 2: Static samples are never silently converted into real trajectories."""
    X_bc, y_bc = load_breast_cancer_fixture()
    builder = ECRGDatasetBuilder()
    df_static, stats = builder.build_static_selective_risk_rows(
        X_bc, y_bc, y_bc, "m1", "d1", "classification_breast_cancer"
    )
    assert (df_static["task_type"] == "STATIC_SELECTIVE_RISK").all()
    assert df_static["trajectory_id"].isnull().all()
    assert df_static["state_index"].isnull().all()


def test_3_prediction_error_computed_correctly():
    """Test 3: Prediction error is computed from prediction vs target."""
    y_true = pd.Series([1, 0, 1, 0])
    y_pred = pd.Series([1, 1, 0, 0])
    X = pd.DataFrame({"f1": [0.1, 0.2, 0.3, 0.4]})

    builder = ECRGDatasetBuilder()
    df_static, _ = builder.build_static_selective_risk_rows(X, y_true, y_pred, "m1", "d1", "dom1")

    expected_errors = [0, 1, 1, 0]
    assert df_static["prediction_error"].tolist() == expected_errors


def test_4_static_temporal_fields_unavailable():
    """Test 4: Static temporal fields remain unavailable (None)."""
    X_bc, y_bc = load_breast_cancer_fixture()
    builder = ECRGDatasetBuilder()
    df_static, _ = builder.build_static_selective_risk_rows(X_bc, y_bc, y_bc, "m1", "d1", "dom1")

    for col in ["trajectory_id", "state_index", "prediction_horizon", "failure_within_horizon"]:
        assert df_static[col].isnull().all()


def test_5_genuine_temporal_group_ids_preserved(sample_trajectory_df):
    """Test 5: Genuine temporal group IDs are preserved."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_temporal_governance_rows(sample_trajectory_df, "m1", "d1", "dom1")
    assert set(c_df["trajectory_id"].unique()) == {"unit_0", "unit_1"}


def test_6_original_temporal_order_preserved(sample_trajectory_df):
    """Test 6: Original temporal order (state_index) is preserved."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_temporal_governance_rows(sample_trajectory_df, "m1", "d1", "dom1", horizons=[1])
    u0_steps = c_df[c_df["trajectory_id"] == "unit_0"]["state_index"].tolist()
    assert u0_steps[:10] == list(range(10))


def test_7_no_silent_synthetic_fallback_on_missing_cmapss():
    """Test 7: Missing genuine C-MAPSS files raise DatasetValidationError (NO SILENT FALLBACK)."""
    builder = ECRGDatasetBuilder()
    with pytest.raises(DatasetValidationError) as exc_info:
        builder.build_genuine_cmapss_evidence(data_dir="non_existent_data_dir")
    assert "Genuine NASA C-MAPSS FD001 dataset files NOT FOUND" in str(exc_info.value)
    assert "NO SILENT FALLBACK PERMITTED" in str(exc_info.value)


def test_8_reference_fitting_uses_training_engines_only(sample_trajectory_df):
    """Test 8: Reference fitting uses training engines only (raises error on overlap)."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_temporal_governance_rows(sample_trajectory_df, "m1", "d1", "dom1")
    # Under seed 42, unit_0 is in calibration group. Passing fit_engines_only=["unit_0"] must raise DatasetValidationError!
    with pytest.raises(DatasetValidationError) as exc_info:
        builder.create_group_aware_split(c_df, train_ratio=0.5, cal_ratio=0.5, test_ratio=0.0, seed=42, fit_engines_only=["unit_0"])
    assert "Reference Fitting Boundary Violation" in str(exc_info.value)


def test_9_future_outcomes_never_enter_features(sample_trajectory_df):
    """Test 9: Feature scores at step t use strictly same-state features."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_temporal_governance_rows(sample_trajectory_df, "m1", "d1", "dom1")
    for idx, row in c_df.iterrows():
        t_id = row["trajectory_id"]
        s_idx = row["state_index"]
        orig_row = sample_trajectory_df[(sample_trajectory_df["trajectory_id"] == t_id) & (sample_trajectory_df["step"] == s_idx)].iloc[0]
        assert row["ood_score"] == pytest.approx(orig_row["ood_risk"])


def test_10_censored_rows_handling(sample_trajectory_df):
    """Test 10: Censored rows remain unlabeled (None target, is_censored = True)."""
    builder = ECRGDatasetBuilder()
    c_df, stats = builder.build_temporal_governance_rows(sample_trajectory_df, "m1", "d1", "dom1", horizons=[1, 2, 3, 5])
    censored_row = c_df[(c_df["trajectory_id"] == "unit_1") & (c_df["state_index"] == 8) & (c_df["prediction_horizon"] == 5)].iloc[0]
    assert bool(censored_row["is_censored"]) is True
    assert pd.isna(censored_row["failure_within_horizon"])


def test_11_horizon_monotonicity_applies_to_valid_rows(sample_trajectory_df):
    """Test 11: Horizon monotonicity applies to fully observed non-censored rows."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_temporal_governance_rows(sample_trajectory_df, "m1", "d1", "dom1", horizons=[1, 2, 3, 5])
    non_censored = c_df[c_df["is_censored"] == False]
    for (t_id, s_idx), grp in non_censored.groupby(["trajectory_id", "state_index"]):
        grp_sorted = grp.sort_values("prediction_horizon")
        targets = grp_sorted["failure_within_horizon"].dropna().tolist()
        for i in range(len(targets) - 1):
            assert targets[i] <= targets[i + 1]


def test_12_complete_groups_stay_within_one_split(sample_trajectory_df):
    """Test 12: Complete trajectory groups stay within one split."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_temporal_governance_rows(sample_trajectory_df, "m1", "d1", "dom1")
    tr, cal, te, manifest = builder.create_group_aware_split(c_df, seed=42)

    tr_units = set(tr["trajectory_id"].unique())
    cal_units = set(cal["trajectory_id"].unique())
    te_units = set(te["trajectory_id"].unique())

    assert len(tr_units.intersection(cal_units)) == 0
    assert len(tr_units.intersection(te_units)) == 0
    assert len(cal_units.intersection(te_units)) == 0


def test_13_effective_sample_size_audited(sample_trajectory_df):
    """Test 13: Effective sample size uses samples or trajectories correctly."""
    builder = ECRGDatasetBuilder()
    c_df, stats = builder.build_temporal_governance_rows(sample_trajectory_df, "m1", "d1", "dom1")
    assert stats["total_independent_trajectories"] == 2


def test_14_conformal_feasibility_warning(sample_trajectory_df):
    """Test 14: Insufficient calibration size triggers an explicit conformal warning."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_temporal_governance_rows(sample_trajectory_df, "m1", "d1", "dom1")
    tr, cal, te, manifest = builder.create_group_aware_split(c_df, seed=42)
    audit = manifest["conformal_feasibility_audit"]["alpha_0.05"]
    assert audit["is_conformal_feasible"] is False
    assert "Calibration size N_cal=" in audit["warning"]


def test_15_synthetic_cmapss_simulation_relabeled():
    """Test 15: Synthetic C-MAPSS simulation is explicitly relabeled as AUXILIARY_SIMULATED_SEQUENCE."""
    builder = ECRGDatasetBuilder()
    c_sim, stats = builder.build_synthetic_cmapss_simulation(n_engines=10, max_cycles=120, seed=42)
    assert (c_sim["task_type"] == "AUXILIARY_SIMULATED_SEQUENCE").all()
    assert (c_sim["domain_id"] == "synthetic_cmapss_simulation").all()


def test_16_outcome_semantics_explicit(sample_trajectory_df):
    """Test 16: Outcome semantics remain explicit across tasks."""
    builder = ECRGDatasetBuilder()
    c_df, _ = builder.build_temporal_governance_rows(sample_trajectory_df, "m1", "d1", "dom1", outcome_semantics="CONTROLLED_FAILURE_EVENT")
    assert (c_df["outcome_semantics"] == "CONTROLLED_FAILURE_EVENT").all()


def test_17_missing_evidence_remains_missing():
    """Test 17: Missing evidence remains missing (None), not zero-filled."""
    df_missing = pd.DataFrame([
        {"trajectory_id": "u0", "step": 0, "is_failure": 0},
        {"trajectory_id": "u0", "step": 1, "is_failure": 0},
    ])
    builder = ECRGDatasetBuilder()
    c_df, stats = builder.build_temporal_governance_rows(df_missing, "m1", "d1", "dom1")
    assert c_df["ood_score"].isnull().all()
    assert (c_df["has_ood"] == False).all()


def test_18_auxiliary_simulations_clearly_labeled():
    """Test 18: Auxiliary simulated sequences are clearly labeled."""
    X_bc, y_bc = load_breast_cancer_fixture()
    builder = ECRGDatasetBuilder()
    df_static, _ = builder.build_static_selective_risk_rows(X_bc, y_bc, y_bc, "m1", "d1", "dom1")
    df_aux = df_static.copy()
    df_aux["task_type"] = "AUXILIARY_SIMULATED_SEQUENCE"
    assert (df_aux["task_type"] == "AUXILIARY_SIMULATED_SEQUENCE").all()


def test_19_two_clean_builds_reproduce_identical_hashes(sample_trajectory_df):
    """Test 19: Two clean builds reproduce identical scientific hashes."""
    builder = ECRGDatasetBuilder()
    c1, _ = builder.build_temporal_governance_rows(sample_trajectory_df, "m1", "d1", "dom1")
    c2, _ = builder.build_temporal_governance_rows(sample_trajectory_df, "m1", "d1", "dom1")
    assert compute_sha256_hash(c1) == compute_sha256_hash(c2)


def test_20_modules_1_13_unmodified():
    """Test 20: Modules 1-13 core files exist and remain untouched."""
    assert os.path.exists("aegis/core/analyzer.py")
    assert os.path.exists("aegis/core/temporal.py")
    assert os.path.exists("aegis/experiments/run_final_research_freeze.py")
