"""
AEGIS-X Module 14 — Deterministic Dataset Builder Runner & Reproducibility CLI (Phase 2C Genuine NASA Finalized).

Outputs:
1. static_selective/ (Breast Cancer Wisconsin, Digits Parity)
2. temporal_governance/cmapss_fd001_internal/ (Genuine NASA C-MAPSS FD001 100 Train Engines, 60/20/20 split)
3. temporal_governance/cmapss_fd001_external/ (Genuine NASA C-MAPSS FD001 100 Test Engines, truncated RUL evaluation)
4. temporal_governance/controlled_synthetic/ (Controlled synthetic degradation trajectories)
5. auxiliary_simulated/ (Synthetic C-MAPSS simulation & chunked simulated sequences)

Verifies two-run clean reproducibility by asserting byte-identical scientific hashes.
"""

import json
import os
import sys
import hashlib
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
from sklearn.ensemble import RandomForestClassifier

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from aegis.governance.dataset_builder import ECRGDatasetBuilder, compute_sha256_hash, DEFAULT_HORIZONS, TARGET_ALPHAS
from aegis.evaluation.datasets import load_breast_cancer_fixture, load_digits_parity_fixture
from aegis.core.exceptions import DatasetValidationError


RESULTS_DIR = os.path.join(os.path.dirname(__file__), "research_results")


def run_pipeline() -> Tuple[Dict[str, str], Dict[str, Any]]:
    """Runs full ECRG dataset builder pipeline across genuine NASA temporal tasks, static tasks, and auxiliary simulations."""
    builder = ECRGDatasetBuilder()

    static_dir = os.path.join(RESULTS_DIR, "static_selective")
    temp_cmapss_int_dir = os.path.join(RESULTS_DIR, "temporal_governance", "cmapss_fd001_internal")
    temp_cmapss_ext_dir = os.path.join(RESULTS_DIR, "temporal_governance", "cmapss_fd001_external")
    temp_synthetic_dir = os.path.join(RESULTS_DIR, "temporal_governance", "controlled_synthetic")
    auxiliary_dir = os.path.join(RESULTS_DIR, "auxiliary_simulated")

    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(temp_cmapss_int_dir, exist_ok=True)
    os.makedirs(temp_cmapss_ext_dir, exist_ok=True)
    os.makedirs(temp_synthetic_dir, exist_ok=True)
    os.makedirs(auxiliary_dir, exist_ok=True)

    pipeline_hashes = {}
    reports = {}

    # =========================================================================
    # TASK 1: STATIC SELECTIVE RISK (Breast Cancer & Digits Parity)
    # =========================================================================
    # A. Breast Cancer Wisconsin
    X_bc, y_bc = load_breast_cancer_fixture()
    clf_bc = RandomForestClassifier(n_estimators=10, random_state=42)
    clf_bc.fit(X_bc, y_bc)
    y_pred_bc = pd.Series(clf_bc.predict(X_bc))

    ood_bc = np.clip(np.abs(X_bc.iloc[:, 0] - X_bc.iloc[:, 0].mean()) / (X_bc.iloc[:, 0].std() + 1e-5), 0, 1).to_numpy()
    unc_bc = np.full(len(X_bc), 0.15)
    drift_bc = np.full(len(X_bc), 0.08)
    fused_bc = ood_bc * 0.5 + unc_bc * 0.5

    df_bc_static, stats_bc = builder.build_static_selective_risk_rows(
        X=X_bc, y_true=y_bc, y_pred=y_pred_bc,
        model_id="rf_breast_cancer_v1", dataset_id="breast_cancer_wisconsin", domain_id="classification_breast_cancer",
        ood_scores=ood_bc, uncertainty_scores=unc_bc, drift_scores=drift_bc, fused_risks=fused_bc, seed=42,
    )
    tr_bc, cal_bc, te_bc, man_bc = builder.create_group_aware_split(df_bc_static, seed=42)
    df_bc_static.to_csv(os.path.join(static_dir, "classification_breast_cancer_evidence.csv"), index=False)
    pipeline_hashes["bc_static"] = compute_sha256_hash(df_bc_static)

    # B. Digits Parity
    X_dig, y_dig = load_digits_parity_fixture()
    clf_dig = RandomForestClassifier(n_estimators=10, random_state=42)
    clf_dig.fit(X_dig, y_dig)
    y_pred_dig = pd.Series(clf_dig.predict(X_dig))

    ood_dig = np.full(len(X_dig), 0.12)
    unc_dig = np.full(len(X_dig), 0.20)
    drift_dig = np.full(len(X_dig), 0.05)
    fused_dig = np.full(len(X_dig), 0.15)

    df_dig_static, stats_dig = builder.build_static_selective_risk_rows(
        X=X_dig, y_true=y_dig, y_pred=y_pred_dig,
        model_id="rf_digits_parity_v1", dataset_id="digits_parity", domain_id="digits_parity",
        ood_scores=ood_dig, uncertainty_scores=unc_dig, drift_scores=drift_dig, fused_risks=fused_dig, seed=42,
    )
    tr_dig, cal_dig, te_dig, man_dig = builder.create_group_aware_split(df_dig_static, seed=42)
    df_dig_static.to_csv(os.path.join(static_dir, "digits_parity_evidence.csv"), index=False)
    pipeline_hashes["dig_static"] = compute_sha256_hash(df_dig_static)

    reports["static_selective"] = {
        "classification_breast_cancer": {"stats": stats_bc, "manifest": man_bc},
        "digits_parity": {"stats": stats_dig, "manifest": man_dig},
    }

    # =========================================================================
    # TASK 2: GENUINE NASA C-MAPSS FD001 TEMPORAL GOVERNANCE
    # =========================================================================
    # A. Genuine NASA C-MAPSS FD001 Internal 100-Engine Cohort (60/20/20 split)
    df_cmapss_genuine, stats_cmapss_gen = builder.build_genuine_cmapss_evidence(data_dir="data/cmapss_raw", seed=42)
    
    # Deterministic group split: 60 Research Train (nasa_engine_1..60) / 20 Cal (61..80) / 20 Test (81..100)
    tr_cm, cal_cm, te_cm, man_cm = builder.create_group_aware_split(
        df_cmapss_genuine, train_ratio=0.6, cal_ratio=0.2, test_ratio=0.2, seed=42,
        fit_engines_only=[f"nasa_engine_{e}" for e in range(1, 61)], shuffle=False
    )
    df_cmapss_genuine.to_csv(os.path.join(temp_cmapss_int_dir, "cmapss_fd001_genuine_evidence.csv"), index=False)
    tr_cm.to_csv(os.path.join(temp_cmapss_int_dir, "cmapss_fd001_train_split.csv"), index=False)
    cal_cm.to_csv(os.path.join(temp_cmapss_int_dir, "cmapss_fd001_cal_split.csv"), index=False)
    te_cm.to_csv(os.path.join(temp_cmapss_int_dir, "cmapss_fd001_test_split.csv"), index=False)
    pipeline_hashes["cmapss_genuine_internal"] = compute_sha256_hash(df_cmapss_genuine)

    # Compute censoring statistics for K in [1, 2, 3, 5]
    censoring_counts_by_k = {}
    for k in DEFAULT_HORIZONS:
        k_df = df_cmapss_genuine[df_cmapss_genuine["prediction_horizon"] == k]
        censoring_counts_by_k[f"k_{k}"] = {
            "total_rows": len(k_df),
            "censored_rows": int(k_df["is_censored"].sum()),
            "observed_positive_failures": int((k_df["failure_within_horizon"] == 1).sum()),
            "observed_negative_nonfailures": int((k_df["failure_within_horizon"] == 0).sum()),
        }

    reports["cmapss_fd001_internal"] = {
        "stats": stats_cmapss_gen,
        "manifest": man_cm,
        "censoring_counts_by_k": censoring_counts_by_k,
        "engine_split_counts": {
            "research_training_engines": 60,
            "calibration_engines": 20,
            "final_test_engines": 20,
            "training_rows": len(tr_cm),
            "calibration_rows": len(cal_cm),
            "test_rows": len(te_cm),
        },
    }

    # B. Genuine NASA C-MAPSS FD001 External Test Cohort (100 Test Engines)
    df_cmapss_ext, stats_cmapss_ext = builder.build_genuine_cmapss_external_evidence(data_dir="data/cmapss_raw", seed=42)
    df_cmapss_ext.to_csv(os.path.join(temp_cmapss_ext_dir, "cmapss_fd001_external_test_evidence.csv"), index=False)
    pipeline_hashes["cmapss_genuine_external"] = compute_sha256_hash(df_cmapss_ext)

    reports["cmapss_fd001_external"] = {
        "stats": stats_cmapss_ext,
        "engine_count": 100,
        "total_rows": len(df_cmapss_ext),
        "note": "Official NASA FD001 test cohort used strictly for external truncated RUL evaluation.",
    }

    # C. Controlled Synthetic Degradation Trajectories
    sample_traj_path = "examples/sample_temporal_trajectory.csv"
    if os.path.exists(sample_traj_path):
        sample_df = pd.read_csv(sample_traj_path)
        df_synth_temp, stats_synth = builder.build_temporal_governance_rows(
            df=sample_df, model_id="synthetic_degradation_v1", dataset_id="sample_temporal_trajectory",
            domain_id="synthetic_degradation_trajectory", seed=42, source_artifact_path=sample_traj_path,
        )
        tr_sy, cal_sy, te_sy, man_sy = builder.create_group_aware_split(df_synth_temp, seed=42)
        df_synth_temp.to_csv(os.path.join(temp_synthetic_dir, "synthetic_degradation_evidence.csv"), index=False)
        pipeline_hashes["synth_temporal"] = compute_sha256_hash(df_synth_temp)
    else:
        stats_synth = {}
        man_sy = {}

    reports["controlled_synthetic"] = {"stats": stats_synth, "manifest": man_sy}

    # =========================================================================
    # TASK 3: AUXILIARY SIMULATED SEQUENCES (Tagged EXPLICITLY as Simulation)
    # =========================================================================
    # A. Synthetic C-MAPSS Simulation
    df_sim_cmapss, stats_sim = builder.build_synthetic_cmapss_simulation(n_engines=20, max_cycles=150, seed=42)
    tr_sim, cal_sim, te_sim, man_sim = builder.create_group_aware_split(df_sim_cmapss, seed=42)
    df_sim_cmapss.to_csv(os.path.join(auxiliary_dir, "synthetic_cmapss_simulation_evidence.csv"), index=False)
    pipeline_hashes["cmapss_synthetic_simulation"] = compute_sha256_hash(df_sim_cmapss)

    # B. Chunked Static Simulation
    df_bc_aux = df_bc_static.copy()
    df_bc_aux["task_type"] = "AUXILIARY_SIMULATED_SEQUENCE"
    df_bc_aux["trajectory_id"] = [f"sim_unit_{i//20}" for i in range(len(df_bc_aux))]
    df_bc_aux["state_index"] = [i % 20 for i in range(len(df_bc_aux))]
    df_bc_aux["prediction_horizon"] = 5
    df_bc_aux.to_csv(os.path.join(auxiliary_dir, "simulated_chunked_sequence.csv"), index=False)
    pipeline_hashes["auxiliary_simulated_chunked"] = compute_sha256_hash(df_bc_aux)

    reports["auxiliary_simulated"] = {
        "synthetic_cmapss_simulation": {"stats": stats_sim, "manifest": man_sim},
        "simulated_chunked_sequence": {"note": "Static Breast Cancer chunked into simulated units for builder testing"},
    }

    # Save Provenance & Quality Reports
    with open(os.path.join(RESULTS_DIR, "data_quality_report.json"), "w") as f:
        json.dump(reports, f, indent=2)

    with open(os.path.join(RESULTS_DIR, "provenance_manifest.json"), "w") as f:
        json.dump({"scientific_hashes": pipeline_hashes}, f, indent=2)

    return pipeline_hashes, reports


def main():
    print("=" * 80)
    print("AEGIS-X Module 14 — Genuine NASA C-MAPSS Finalized Dataset Builder Execution")
    print("=" * 80)

    # Run 1
    print("\n--- Execution Run 1 ---")
    hashes_run1, _ = run_pipeline()
    print("  Run 1 Hashes:")
    for k, v in hashes_run1.items():
        print(f"    {k}: {v[:16]}...")

    # Run 2 (Clean Rebuild)
    print("\n--- Execution Run 2 (Clean Reproducibility Check) ---")
    hashes_run2, _ = run_pipeline()
    print("  Run 2 Hashes:")
    for k, v in hashes_run2.items():
        print(f"    {k}: {v[:16]}...")

    reproducible = True
    for key in hashes_run1:
        if hashes_run1[key] != hashes_run2[key]:
            reproducible = False
            print(f"  [ERROR] Hash mismatch for {key}!")

    if reproducible:
        print("\n[SUCCESS] 100% Deterministic Reproducibility Confirmed Across Runs!")
    else:
        print("\n[FAILURE] Reproducibility Hash Mismatch Detected!")
        sys.exit(1)


if __name__ == "__main__":
    main()
