"""
AEGIS-X Module 14 — Deterministic Dataset Builder Runner & Reproducibility CLI (Phase 2B Repaired).

Outputs:
1. static_selective/ (Breast Cancer Wisconsin, Digits Parity)
2. temporal_governance/ (NASA C-MAPSS Turbofan, Synthetic Degradation Trajectories)
3. auxiliary_simulated/ (Auxiliary simulated sequences)

Verifies two-run clean reproducibility by asserting byte-identical scientific hashes.
"""

import json
import os
import sys
import hashlib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from aegis.governance.dataset_builder import ECRGDatasetBuilder, compute_sha256_hash, DEFAULT_HORIZONS, TARGET_ALPHAS
from aegis.evaluation.datasets import load_breast_cancer_fixture, load_digits_parity_fixture


RESULTS_DIR = os.path.join(os.path.dirname(__file__), "research_results")


def run_pipeline() -> Tuple[Dict[str, str], Dict[str, Any]]:
    """Runs full ECRG dataset builder pipeline across static, temporal, and auxiliary tasks."""
    builder = ECRGDatasetBuilder()

    static_dir = os.path.join(RESULTS_DIR, "static_selective")
    temporal_dir = os.path.join(RESULTS_DIR, "temporal_governance")
    auxiliary_dir = os.path.join(RESULTS_DIR, "auxiliary_simulated")

    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(temporal_dir, exist_ok=True)
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

    # Synthetic reliability scores for static demonstration
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
    # TASK 2: TEMPORAL GOVERNANCE (NASA C-MAPSS & Synthetic Trajectories)
    # =========================================================================
    # A. NASA C-MAPSS Turbofan Degradation (Principal Temporal Source)
    df_cmapss_temp, stats_cmapss = builder.build_cmapss_evidence(n_engines=20, max_cycles=150, seed=42)
    tr_cm, cal_cm, te_cm, man_cm = builder.create_group_aware_split(df_cmapss_temp, seed=42)
    df_cmapss_temp.to_csv(os.path.join(temporal_dir, "cmapss_turbofan_evidence.csv"), index=False)
    pipeline_hashes["cmapss_temporal"] = compute_sha256_hash(df_cmapss_temp)

    # B. Synthetic Degradation Trajectories
    sample_traj_path = "examples/sample_temporal_trajectory.csv"
    if os.path.exists(sample_traj_path):
        sample_df = pd.read_csv(sample_traj_path)
        df_synth_temp, stats_synth = builder.build_temporal_governance_rows(
            df=sample_df, model_id="synthetic_degradation_v1", dataset_id="sample_temporal_trajectory",
            domain_id="synthetic_degradation_trajectory", seed=42, source_artifact_path=sample_traj_path,
        )
        tr_sy, cal_sy, te_sy, man_sy = builder.create_group_aware_split(df_synth_temp, seed=42)
        df_synth_temp.to_csv(os.path.join(temporal_dir, "synthetic_degradation_evidence.csv"), index=False)
        pipeline_hashes["synth_temporal"] = compute_sha256_hash(df_synth_temp)
        reports["temporal_governance"] = {
            "cmapss_turbofan": {"stats": stats_cmapss, "manifest": man_cm},
            "synthetic_degradation": {"stats": stats_synth, "manifest": man_sy},
        }

    # =========================================================================
    # TASK 3: AUXILIARY SIMULATED SEQUENCES (For Builder Sanity Testing Only)
    # =========================================================================
    # Retain chunked Breast Cancer sequence tagged strictly as AUXILIARY_SIMULATED_SEQUENCE
    df_bc_aux = df_bc_static.copy()
    df_bc_aux["task_type"] = "AUXILIARY_SIMULATED_SEQUENCE"
    df_bc_aux["trajectory_id"] = [f"sim_unit_{i//20}" for i in range(len(df_bc_aux))]
    df_bc_aux["state_index"] = [i % 20 for i in range(len(df_bc_aux))]
    df_bc_aux["prediction_horizon"] = 5
    df_bc_aux.to_csv(os.path.join(auxiliary_dir, "simulated_chunked_sequence.csv"), index=False)
    pipeline_hashes["auxiliary_simulated"] = compute_sha256_hash(df_bc_aux)

    # Save Provenance & Quality Reports
    with open(os.path.join(RESULTS_DIR, "data_quality_report.json"), "w") as f:
        json.dump(reports, f, indent=2)

    with open(os.path.join(RESULTS_DIR, "provenance_manifest.json"), "w") as f:
        json.dump({"scientific_hashes": pipeline_hashes}, f, indent=2)

    return pipeline_hashes, reports


def main():
    print("=" * 80)
    print("AEGIS-X Module 14 — Phase 2B Scientific Dataset Builder Execution")
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

    # Assert 100% Byte-Identical Reproducibility
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
