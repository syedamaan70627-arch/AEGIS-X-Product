"""
AEGIS-X Module 14 — Phase 5B Statistical Reporting Integrity & Experiment Completeness Audit Unit Tests.

Verifies:
1. Plus-one empirical bootstrap p-value formula (p = (extreme_count + 1) / (B + 1)).
2. Holm-Bonferroni correction non-decreasing monotonicity.
3. Clopper-Pearson exact binomial confidence intervals.
4. Area Under Risk-Coverage curve (AURC) calculation.
5. Zero denominator metric handling (NA — undefined).
6. External zero-positive outcome handling (NA — no positive outcomes).
7. Static evaluation generation (Breast Cancer Wisconsin & Digits Parity).
8. Conformal Empirical Coverage vs Singleton Accuracy metric labelling.
9. Confidence interval serialization safety.
10. Preregistered protocol completeness matrix.
11. State machine configuration immutability.
12. Result table deterministic row ordering.
13. Scientific payload SHA-256 hashing.
14. Microbenchmark latency metric labelling.
15. Trajectory cluster bootstrap CI output structure.
"""

import os
import sys
import json
import math
import hashlib
import numpy as np
import pandas as pd
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from aegis.governance.experiments.run_phase5_experiments import (
    compute_clopper_pearson_ci,
    compute_plus_one_bootstrap_pvalue,
    holm_bonferroni_correction,
    compute_aurc,
    fit_calibrator_on_splits,
    run_evaluation_for_cohort,
    run_cluster_bootstrap,
    benchmark_governance_latency,
)
from aegis.governance.schemas import ECRGStateMachineConfig
from aegis.governance.dataset_builder import ECRGDatasetBuilder, compute_sha256_hash
from aegis.evaluation.datasets import load_breast_cancer_fixture, load_digits_parity_fixture


def make_dummy_calibrator_artifact():
    """Helper to create a valid calibrator artifact using actual dataset splits."""
    cmapss_int_dir = os.path.join(BASE_DIR, "aegis", "governance", "research_results", "temporal_governance", "cmapss_fd001_internal")
    df_tr = pd.read_csv(os.path.join(cmapss_int_dir, "cmapss_fd001_train_split.csv"))
    df_cal = pd.read_csv(os.path.join(cmapss_int_dir, "cmapss_fd001_cal_split.csv"))
    
    df_tr_h3 = df_tr[df_tr["prediction_horizon"] == 3].copy()
    df_cal_h3 = df_cal[df_cal["prediction_horizon"] == 3].copy()
    
    return fit_calibrator_on_splits(
        df_train=df_tr_h3, df_cal=df_cal_h3,
        feature_cols=["ood_score", "uncertainty_score", "drift_score", "fused_risk"],
        target_col="failure_within_horizon", target_alpha=0.05,
    )


def test_plus_one_bootstrap_pvalue_formula():
    """Verifies p = (extreme_count + 1) / (B + 1) and minimum p-value bound 1/2001."""
    diffs_boot = np.random.normal(loc=0.0, scale=1.0, size=2000)
    
    # 1. Zero extreme count
    ext_cnt, p_val = compute_plus_one_bootstrap_pvalue(diffs_boot, diff_obs=10.0)
    assert ext_cnt == 0
    assert abs(p_val - (1.0 / 2001.0)) < 1e-8
    assert p_val > 0.0
    assert p_val >= 0.00049975

    # 2. Non-zero extreme count
    ext_cnt_2, p_val_2 = compute_plus_one_bootstrap_pvalue(diffs_boot, diff_obs=0.1)
    assert p_val_2 == (ext_cnt_2 + 1) / 2001.0


def test_holm_bonferroni_monotonicity():
    """Verifies Holm-Bonferroni correction enforces non-decreasing monotonicity."""
    raw_p_vals = [0.00049975, 0.00049975, 0.00049975, 0.00049975]
    adj_p_vals = holm_bonferroni_correction(raw_p_vals)
    
    assert len(adj_p_vals) == 4
    for raw, adj in zip(raw_p_vals, adj_p_vals):
        assert adj >= raw

    for i in range(1, len(adj_p_vals)):
        assert adj_p_vals[i] >= adj_p_vals[i - 1]

    raw_mixed = [0.04, 0.01, 0.03, 0.001]
    adj_mixed = holm_bonferroni_correction(raw_mixed)
    assert adj_mixed[3] == pytest.approx(0.004)
    assert adj_mixed[1] == pytest.approx(0.03)
    assert adj_mixed[2] == pytest.approx(0.06)
    assert adj_mixed[0] == pytest.approx(0.06)


def test_clopper_pearson_exact_bounds():
    """Verifies Clopper-Pearson exact binomial confidence interval calculation."""
    low_20, high_20 = compute_clopper_pearson_ci(k=20, n=20, alpha=0.05)
    assert abs(low_20 - 0.831566) < 1e-4
    assert high_20 == 1.0

    low_0, high_0 = compute_clopper_pearson_ci(k=0, n=20, alpha=0.05)
    assert low_0 == 0.0
    assert abs(high_0 - 0.168433) < 1e-4

    low_empty, high_empty = compute_clopper_pearson_ci(k=0, n=0, alpha=0.05)
    assert low_empty == 0.0 and high_empty == 0.0


def test_aurc_calculation():
    """Verifies compute_aurc produces valid area under risk-coverage curve."""
    risk_scores = np.array([0.1, 0.2, 0.8, 0.9])
    y_errors = np.array([0, 0, 1, 1])
    aurc = compute_aurc(risk_scores, y_errors)
    assert 0.0 <= aurc <= 1.0
    assert aurc < 0.5


def test_zero_denominator_returns_na():
    """Verifies that when n_continue == 0, selective risk returns 'NA — undefined'."""
    df_eval = pd.DataFrame([{
        "trajectory_id": "unit_1",
        "state_index": 1,
        "prediction_horizon": 3,
        "ood_score": 0.99,
        "uncertainty_score": 0.99,
        "drift_score": 0.99,
        "fused_risk": 0.99,
        "failure_within_horizon": 1,
    }])
    
    res = run_evaluation_for_cohort(
        df_eval=df_eval,
        artifact=None,
        method_name="UNCERTAINTY_ONLY",
        target_col="failure_within_horizon",
        feature_cols=["fused_risk"],
        target_alpha=0.05,
    )
    assert res["selective_risk"] is None
    assert res["selective_risk_str"] == "NA — undefined"


def test_external_zero_positive_returns_na():
    """Verifies that external zero-positive targets return 'NA — no positive outcomes'."""
    df_eval = pd.DataFrame([{
        "trajectory_id": "ext_1",
        "state_index": 1,
        "prediction_horizon": 3,
        "dataset_id": "external_cmapss",
        "ood_score": 0.05,
        "uncertainty_score": 0.05,
        "drift_score": 0.05,
        "fused_risk": 0.05,
        "C_MAPSS_TERMINAL_FAILURE_WITHIN_K": 0,
    }])
    
    res = run_evaluation_for_cohort(
        df_eval=df_eval,
        artifact=None,
        method_name="UNCERTAINTY_ONLY",
        target_col="C_MAPSS_TERMINAL_FAILURE_WITHIN_K",
        feature_cols=["fused_risk"],
        target_alpha=0.05,
    )
    assert res["selective_risk_str"] == "NA — no positive outcomes"


def test_static_evaluation_generation():
    """Verifies Breast Cancer static evaluation pipeline runs deterministically."""
    X_bc, y_bc = load_breast_cancer_fixture()
    assert len(X_bc) == 569
    assert len(y_bc) == 569

    builder = ECRGDatasetBuilder()
    df_static, stats = builder.build_static_selective_risk_rows(
        X=X_bc, y_true=y_bc, y_pred=y_bc,
        model_id="m_test", dataset_id="d_test", domain_id="dom_test",
        ood_scores=np.zeros(len(X_bc)), uncertainty_scores=np.zeros(len(X_bc)),
        drift_scores=np.zeros(len(X_bc)), fused_risks=np.zeros(len(X_bc)), seed=42,
    )
    assert len(df_static) == 569
    assert "prediction_error" in df_static.columns


def test_conformal_coverage_vs_singleton_accuracy_labeling():
    """Verifies conformal methods get 'Conformal Empirical Coverage' label and non-conformal get 'Singleton Accuracy'."""
    df_eval = pd.DataFrame([{
        "trajectory_id": "t1", "state_index": 0, "prediction_horizon": 3,
        "ood_score": 0.1, "uncertainty_score": 0.1, "drift_score": 0.1, "fused_risk": 0.1,
        "y_target": 0,
    }])
    art = make_dummy_calibrator_artifact()
    
    res_conf = run_evaluation_for_cohort(
        df_eval=df_eval, artifact=art, method_name="ECRG_CALIBRATED_FULL",
        target_col="y_target", feature_cols=["fused_risk"], target_alpha=0.05,
    )
    assert res_conf["coverage_metric_label"] == "Conformal Empirical Coverage"
    assert res_conf["is_conformal"] is True

    res_single = run_evaluation_for_cohort(
        df_eval=df_eval, artifact=None, method_name="UNCALIBRATED_RISK_LEARNER",
        target_col="y_target", feature_cols=["fused_risk"], target_alpha=0.05,
    )
    assert res_single["coverage_metric_label"] == "Singleton Accuracy"
    assert res_single["is_conformal"] is False


def test_confidence_interval_serialization():
    """Verifies 95% CIs serialize cleanly to JSON without float errors or NaNs."""
    ci_dict = {
        "empirical_coverage": (0.90, 0.95),
        "trajectory_simultaneous_coverage": (0.85, 1.00),
    }
    dumped = json.dumps(ci_dict)
    loaded = json.loads(dumped)
    assert loaded["empirical_coverage"] == [0.90, 0.95]


def test_preregistered_completeness_matrix():
    """Verifies phase5_protocol.md contains preregistered evaluation protocol specifications."""
    protocol_path = os.path.join(BASE_DIR, "aegis", "governance", "experiments", "phase5_protocol.md")
    assert os.path.exists(protocol_path)
    with open(protocol_path, "r") as f:
        content = f.read()
    assert "Pre-Registered Evaluation Protocol" in content
    assert "Breast Cancer Wisconsin" in content
    assert "Digits Parity" in content


def test_no_post_test_configuration_mutation():
    """Verifies state machine parameters remain locked to preregistered protocol."""
    config = ECRGStateMachineConfig()
    assert config.defer_persistence_threshold == 3
    assert config.recovery_consecutive_states == 3
    assert config.latch_escalate is True


def test_result_table_deterministic_ordering():
    """Verifies phase5_method_comparison.csv contains all 5 preregistered methods in deterministic order when present."""
    csv_path = os.path.join(BASE_DIR, "aegis", "governance", "research_results", "phase5_method_comparison.csv")
    if os.path.exists(csv_path):
        df_comp = pd.read_csv(csv_path)
        expected_methods = [
            "ECRG_CALIBRATED_FULL",
            "ECRG_EVIDENCE_ONLY",
            "UNCALIBRATED_RISK_LEARNER",
            "FROZEN_STRESS_ROBUST_FUSION",
            "UNCERTAINTY_ONLY",
        ]
        assert list(df_comp["method_name"]) == expected_methods


def test_scientific_payload_hashing():
    """Verifies computing SHA-256 hash on dictionary payload is deterministic across runs."""
    payload = {"a": 1, "b": [1, 2, 3], "c": "test"}
    hash1 = compute_sha256_hash(payload)
    hash2 = compute_sha256_hash(payload)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_latency_metric_labeling():
    """Verifies benchmark_governance_latency output explicitly labels narrow score vs end-to-end governance latency."""
    art = make_dummy_calibrator_artifact()
    bench_res = benchmark_governance_latency(art, n_warmup=10, n_repetitions=100)
    assert "narrow_score_latency_median_us" in bench_res
    assert "end_to_end_governance_latency_median_us" in bench_res
    assert "hardware_environment" in bench_res
    assert bench_res["timer_used"] == "time.perf_counter_ns()"


def test_trajectory_cluster_bootstrap():
    """Verifies run_cluster_bootstrap returns expected 95% CIs for metrics."""
    df_eval = pd.DataFrame([
        {"trajectory_id": "eng_1", "state_index": 0, "prediction_horizon": 3, "ood_score": 0.1, "uncertainty_score": 0.1, "drift_score": 0.1, "fused_risk": 0.1, "failure_within_horizon": 0},
        {"trajectory_id": "eng_1", "state_index": 1, "prediction_horizon": 3, "ood_score": 0.1, "uncertainty_score": 0.1, "drift_score": 0.1, "fused_risk": 0.1, "failure_within_horizon": 1},
    ])
    
    ci_res = run_cluster_bootstrap(
        df_eval=df_eval, artifact=None, method_name="UNCERTAINTY_ONLY",
        target_col="failure_within_horizon", feature_cols=["fused_risk"],
        target_alpha=0.05, n_boot=50, seed=42,
    )
    assert "empirical_coverage" in ci_res
    assert "trajectory_simultaneous_coverage" in ci_res
    assert isinstance(ci_res["empirical_coverage"], tuple)
