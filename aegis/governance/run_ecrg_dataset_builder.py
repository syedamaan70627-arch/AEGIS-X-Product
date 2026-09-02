"""
AEGIS-X Module 14 — Deterministic Dataset Builder Runner & Reproducibility CLI.
Generates canonical evidence datasets, per-domain split manifests, data-quality reports,
provenance manifests, and dataset cards.
"""

import json
import os
import sys
import hashlib
import pandas as pd
import numpy as np

from aegis.governance.dataset_builder import ECRGDatasetBuilder, compute_sha256_hash, DEFAULT_HORIZONS
from aegis.evaluation.datasets import load_breast_cancer_fixture, load_digits_parity_fixture


RESULTS_DIR = os.path.join(os.path.dirname(__file__), "research_results")


def run_builder():
    print("=" * 80)
    print("AEGIS-X Module 14 — Evidence Dataset Builder")
    print("=" * 80)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    builder = ECRGDatasetBuilder()

    domain_datasets = {}
    domain_stats = {}
    domain_manifests = {}

    # 1. Temporal Trajectory Domain (sample_temporal_trajectory.csv)
    sample_traj_path = "examples/sample_temporal_trajectory.csv"
    if os.path.exists(sample_traj_path):
        print(f"\n[Domain 1/3] Loading sample temporal trajectory from {sample_traj_path}...")
        sample_df = pd.read_csv(sample_traj_path)
        c_df1, stats1 = builder.build_canonical_rows_for_df(
            df=sample_df,
            model_id="013245af-9a9a-4e59-9648-0bb135f604d7",
            dataset_id="sample_temporal_trajectory",
            domain_id="synthetic_degradation_trajectory",
            seed=42,
            source_module="Module_12_13_EarlyWarning",
            source_artifact_path=sample_traj_path,
        )
        tr1, cal1, te1, man1 = builder.create_group_aware_split(c_df1, seed=42)
        domain_datasets["synthetic_degradation_trajectory"] = c_df1
        domain_stats["synthetic_degradation_trajectory"] = stats1
        domain_manifests["synthetic_degradation_trajectory"] = man1
        print(f"  -> Generated {len(c_df1)} canonical rows across {stats1['total_trajectories']} trajectories.")
    else:
        print(f"\n[Domain 1/3] Sample trajectory not found at {sample_traj_path}.")

    # 2. Tabular Domain: Breast Cancer Wisconsin Fixture
    print("\n[Domain 2/3] Loading Breast Cancer Wisconsin research fixture...")
    X_bc, y_bc = load_breast_cancer_fixture()
    df_bc = pd.concat([X_bc, y_bc.rename("is_failure")], axis=1)
    # Add dummy synthetic signals for tabular demonstration
    df_bc["ood_risk"] = np.clip(np.abs(df_bc["feature_mean radius"] - df_bc["feature_mean radius"].mean()) / df_bc["feature_mean radius"].std() / 5.0, 0, 1)
    df_bc["uncertainty_risk"] = 0.2
    df_bc["drift_risk"] = 0.1
    df_bc["fused_risk"] = 0.2
    df_bc["trajectory_id"] = [f"unit_{i//20}" for i in range(len(df_bc))]
    df_bc["step"] = [i % 20 for i in range(len(df_bc))]

    c_df2, stats2 = builder.build_canonical_rows_for_df(
        df=df_bc,
        model_id="bc_classifier_v1",
        dataset_id="breast_cancer_wisconsin",
        domain_id="classification_breast_cancer",
        seed=42,
        source_module="Module_12_CrossDomain",
        source_artifact_path="sklearn.datasets.load_breast_cancer",
    )
    tr2, cal2, te2, man2 = builder.create_group_aware_split(c_df2, seed=42)
    domain_datasets["classification_breast_cancer"] = c_df2
    domain_stats["classification_breast_cancer"] = stats2
    domain_manifests["classification_breast_cancer"] = man2
    print(f"  -> Generated {len(c_df2)} canonical rows across {stats2['total_trajectories']} unit trajectories.")

    # 3. Tabular Domain: Digits Parity Fixture
    print("\n[Domain 3/3] Loading Digits Parity research fixture...")
    X_dig, y_dig = load_digits_parity_fixture()
    df_dig = pd.concat([X_dig, y_dig.rename("is_failure")], axis=1)
    df_dig["ood_risk"] = 0.15
    df_dig["uncertainty_risk"] = 0.25
    df_dig["drift_risk"] = 0.10
    df_dig["fused_risk"] = 0.18
    df_dig["trajectory_id"] = [f"unit_{i//25}" for i in range(len(df_dig))]
    df_dig["step"] = [i % 25 for i in range(len(df_dig))]

    c_df3, stats3 = builder.build_canonical_rows_for_df(
        df=df_dig,
        model_id="digits_parity_v1",
        dataset_id="digits_parity",
        domain_id="digits_parity",
        seed=42,
        source_module="Module_12_CrossDomain",
        source_artifact_path="sklearn.datasets.load_digits",
    )
    tr3, cal3, te3, man3 = builder.create_group_aware_split(c_df3, seed=42)
    domain_datasets["digits_parity"] = c_df3
    domain_stats["digits_parity"] = stats3
    domain_manifests["digits_parity"] = man3
    print(f"  -> Generated {len(c_df3)} canonical rows across {stats3['total_trajectories']} unit trajectories.")

    # Save Output Manifests & Data Reports
    print("\n" + "=" * 80)
    print("Writing Research Results, Manifests & Data Quality Reports...")
    print("=" * 80)

    # 1. Builder Config
    builder_config = {
        "builder_version": "1.0.0",
        "config_hash": builder.config_hash,
        "horizons": DEFAULT_HORIZONS,
        "split_ratios": {"train": 0.6, "calibration": 0.2, "test": 0.2},
        "seed": 42,
    }
    with open(os.path.join(RESULTS_DIR, "builder_config.json"), "w") as f:
        json.dump(builder_config, f, indent=2)

    # 2. Data Quality & Availability Report
    quality_report = {
        "summary": "Deterministic data quality and signal availability audit for Module 14 Phase 2.",
        "builder_version": "1.0.0",
        "domains": domain_stats,
    }
    with open(os.path.join(RESULTS_DIR, "data_quality_report.json"), "w") as f:
        json.dump(quality_report, f, indent=2)

    # 3. Split Manifests
    with open(os.path.join(RESULTS_DIR, "split_manifests.json"), "w") as f:
        json.dump(domain_manifests, f, indent=2)

    # 4. Provenance Manifest
    provenance_hashes = {}
    for dname, ddf in domain_datasets.items():
        csv_path = os.path.join(RESULTS_DIR, f"{dname}_evidence.csv")
        ddf.to_csv(csv_path, index=False)
        provenance_hashes[dname] = {
            "csv_filename": f"{dname}_evidence.csv",
            "row_count": len(ddf),
            "sha256_hash": compute_sha256_hash(ddf),
        }

    with open(os.path.join(RESULTS_DIR, "provenance_manifest.json"), "w") as f:
        json.dump({"provenance": provenance_hashes}, f, indent=2)

    # 5. Dataset Card
    dataset_card_content = f"""# AEGIS-X Module 14 Canonical Evidence Dataset Card

**Dataset Version**: 1.0.0  
**Builder Config Hash**: `{builder.config_hash}`  
**Domains Included**: {list(domain_datasets.keys())}  
**Horizons**: K = [1, 2, 3, 5] controlled_degradation_states  

## Overview
This canonical evidence dataset combines reliability signals, detector diagnostics, and forward-looking ground-truth targets across synthetic degradation trajectories and tabular cross-domain validation fixtures.

## Domain Breakdown
- **synthetic_degradation_trajectory**: {len(domain_datasets.get('synthetic_degradation_trajectory', []))} rows
- **classification_breast_cancer**: {len(domain_datasets.get('classification_breast_cancer', []))} rows
- **digits_parity**: {len(domain_datasets.get('digits_parity', []))} rows

## Split Protocol
Group-aware 60/20/20 partitioning by trajectory ID with 100% zero-overlap verification.
"""
    with open(os.path.join(RESULTS_DIR, "dataset_card.md"), "w") as f:
        f.write(dataset_card_content)

    print("\n[SUCCESS] Builder completed successfully! Artifacts written to:")
    print(f"  {RESULTS_DIR}")


if __name__ == "__main__":
    run_builder()
