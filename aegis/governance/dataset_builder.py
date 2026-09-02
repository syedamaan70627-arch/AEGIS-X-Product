"""
AEGIS-X Module 14 — Evidence-Calibrated Reliability Governance (ECRG)
Deterministic, Leakage-Safe Research Evidence Dataset Builder.

Constructs canonical long-format evidence rows for:
model x dataset/domain x seed x trajectory x state_index x horizon (K in {1, 2, 3, 5}).
"""

import hashlib
import json
import os
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd

from aegis.core.exceptions import DatasetValidationError
from aegis.core.temporal import compute_future_failure_within_n


BUILDER_VERSION = "1.0.0"
DEFAULT_HORIZONS = [1, 2, 3, 5]


def compute_sha256_hash(data: Union[str, bytes, pd.DataFrame]) -> str:
    """Computes deterministic SHA-256 hash for strings, bytes, or pandas DataFrames."""
    if isinstance(data, pd.DataFrame):
        content = data.to_csv(index=False).encode("utf-8")
    elif isinstance(data, str):
        content = data.encode("utf-8")
    else:
        content = data
    return hashlib.sha256(content).hexdigest()


class ECRGDatasetBuilder:
    """
    Deterministic, Leakage-Safe Evidence Dataset Builder for AEGIS-X Module 14.
    """

    def __init__(self, config_hash: Optional[str] = None):
        self.config_hash = config_hash or hashlib.sha256(b"ECRG_BUILDER_V1_CONFIG").hexdigest()[:16]

    def build_canonical_rows_for_df(
        self,
        df: pd.DataFrame,
        model_id: str,
        dataset_id: str,
        domain_id: str,
        seed: int = 42,
        source_module: str = "Modules_1-13_Harness",
        source_artifact_path: str = "raw_source",
        horizons: List[int] = DEFAULT_HORIZONS,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Constructs canonical long-format evidence rows for a given trajectory/domain DataFrame.
        Enforces horizon monotonicity, censoring policies, and explicit availability flags.
        """
        df = df.copy()
        source_hash = compute_sha256_hash(df)

        # Detect schema presence
        has_trajectory = "trajectory_id" in df.columns
        has_step = "step" in df.columns or "sequence_step" in df.columns
        has_ground_truth = "is_failure" in df.columns or "target" in df.columns

        if not has_trajectory:
            df["trajectory_id"] = "single_unit"
        if "step" not in df.columns and "sequence_step" in df.columns:
            df["step"] = df["sequence_step"]
        if not has_step:
            df["step"] = np.arange(len(df))

        # Standardize detector signal columns if present
        ood_col = "ood_risk" if "ood_risk" in df.columns else ("ood_score" if "ood_score" in df.columns else None)
        unc_col = "uncertainty_risk" if "uncertainty_risk" in df.columns else ("uncertainty_score" if "uncertainty_score" in df.columns else None)
        drift_col = "drift_risk" if "drift_risk" in df.columns else ("drift_score" if "drift_score" in df.columns else None)
        fused_col = "fused_risk" if "fused_risk" in df.columns else None
        stress_fused_col = "stress_robust_fused_risk" if "stress_robust_fused_risk" in df.columns else fused_col

        has_ood = ood_col is not None
        has_unc = unc_col is not None
        has_drift = drift_col is not None
        has_fused = fused_col is not None
        has_mem = "memory_similarity" in df.columns
        has_temp = "temporal_failure_probability" in df.columns
        has_ew = "early_warning_state" in df.columns

        # Ensure ground-truth target is defined if available
        if has_ground_truth:
            gt_col = "is_failure" if "is_failure" in df.columns else "target"
            df["is_failure_clean"] = df[gt_col].fillna(0).astype(int)
        else:
            df["is_failure_clean"] = None

        canonical_records = []
        invalidation_count = 0
        censored_count = 0

        # Process per trajectory
        for traj_id, group in df.groupby("trajectory_id", sort=False):
            group = group.sort_values("step").reset_index(drop=True)
            n_steps = len(group)

            # Compute failure event index if present
            failure_indices = group.index[group["is_failure_clean"] == 1].tolist() if has_ground_truth else []
            first_fail_idx = failure_indices[0] if len(failure_indices) > 0 else None
            eventual_fail = 1 if len(failure_indices) > 0 else 0 if has_ground_truth else None

            # Pre-compute future failure targets for each horizon K
            horizon_targets = {}
            if has_ground_truth:
                for k in horizons:
                    horizon_targets[k] = compute_future_failure_within_n(group["is_failure_clean"], k).to_numpy()

            for i in range(n_steps):
                step_idx = int(group.loc[i, "step"])

                # Check state monotonicity across horizons
                if has_ground_truth:
                    h_vals = [horizon_targets[k][i] for k in sorted(horizons)]
                    for idx_h in range(len(h_vals) - 1):
                        if h_vals[idx_h] > h_vals[idx_h + 1]:
                            raise DatasetValidationError(
                                f"Monotonicity violation at trajectory {traj_id}, step {step_idx}: "
                                f"Failure_Within_{sorted(horizons)[idx_h]} ({h_vals[idx_h]}) > "
                                f"Failure_Within_{sorted(horizons)[idx_h+1]} ({h_vals[idx_h+1]})"
                            )

                # Compute remaining states before failure if eventual failure occurs
                if first_fail_idx is not None and first_fail_idx >= i:
                    states_remaining = int(first_fail_idx - i)
                else:
                    states_remaining = None

                # Compute same-state signal disagreement if signals exist
                avail_signals = []
                if has_ood and pd.notna(group.loc[i, ood_col]): avail_signals.append(float(group.loc[i, ood_col]))
                if has_unc and pd.notna(group.loc[i, unc_col]): avail_signals.append(float(group.loc[i, unc_col]))
                if has_drift and pd.notna(group.loc[i, drift_col]): avail_signals.append(float(group.loc[i, drift_col]))

                signal_disagreement = float(np.std(avail_signals)) if len(avail_signals) >= 2 else 0.0

                for k in horizons:
                    # Deterministic row ID
                    row_key = f"{model_id}:{domain_id}:{seed}:{traj_id}:{step_idx}:{k}"
                    row_id = hashlib.sha256(row_key.encode("utf-8")).hexdigest()[:24]

                    # Censoring check: trajectory ending before step_idx + k without failure
                    censored = False
                    if has_ground_truth:
                        target_k = int(horizon_targets[k][i])
                        if (i + k >= n_steps) and (target_k == 0) and (eventual_fail == 0):
                            # Right-censored without failure
                            censored = True
                            censored_count += 1
                    else:
                        target_k = None

                    record = {
                        "row_id": row_id,
                        "source_module": source_module,
                        "source_artifact_path": source_artifact_path,
                        "source_artifact_hash": source_hash,
                        "model_id": model_id,
                        "dataset_id": dataset_id,
                        "domain_id": domain_id,
                        "seed": seed,
                        "trajectory_id": str(traj_id),
                        "state_index": step_idx,
                        "prediction_horizon": k,
                        "extraction_timestamp": "2026-09-02T20:45:00Z",
                        "builder_version": BUILDER_VERSION,
                        "config_hash": self.config_hash,
                        # Raw Scores (Nullable, No Global Scaling)
                        "ood_score": float(group.loc[i, ood_col]) if has_ood and pd.notna(group.loc[i, ood_col]) else None,
                        "uncertainty_score": float(group.loc[i, unc_col]) if has_unc and pd.notna(group.loc[i, unc_col]) else None,
                        "drift_score": float(group.loc[i, drift_col]) if has_drift and pd.notna(group.loc[i, drift_col]) else None,
                        "fused_risk": float(group.loc[i, fused_col]) if has_fused and pd.notna(group.loc[i, fused_col]) else None,
                        "stress_robust_fused_risk": float(group.loc[i, stress_fused_col]) if stress_fused_col and pd.notna(group.loc[i, stress_fused_col]) else None,
                        "signal_disagreement": signal_disagreement,
                        "ood_drift_redundancy": None,  # Defer learning correlations to training split
                        "stress_robustness": float(group.loc[i, "stress_robustness"]) if "stress_robustness" in group.columns else None,
                        "fault_sensitivity": float(group.loc[i, "fault_sensitivity"]) if "fault_sensitivity" in group.columns else None,
                        "memory_similarity": float(group.loc[i, "memory_similarity"]) if has_mem else None,
                        "temporal_failure_probability": float(group.loc[i, "temporal_failure_probability"]) if has_temp else None,
                        "early_warning_state": str(group.loc[i, "early_warning_state"]) if has_ew else "NORMAL",
                        # Explicit Availability Flags
                        "has_ood": has_ood,
                        "has_uncertainty": has_unc,
                        "has_drift": has_drift,
                        "has_fused_risk": has_fused,
                        "has_memory": has_mem,
                        "has_temporal": has_temp,
                        "has_early_warning": has_ew,
                        "has_ground_truth": has_ground_truth,
                        "is_censored": censored,
                        # Ground-Truth Targets
                        "eventual_failure": eventual_fail,
                        "failure_event_index": first_fail_idx,
                        "failure_within_horizon": target_k,
                        "states_remaining_before_failure": states_remaining,
                    }
                    canonical_records.append(record)

        canonical_df = pd.DataFrame(canonical_records)

        # Validation Audit Metrics
        stats = {
            "model_id": str(model_id),
            "dataset_id": str(dataset_id),
            "domain_id": str(domain_id),
            "seed": int(seed),
            "source_artifact_hash": str(source_hash),
            "total_trajectories": int(df["trajectory_id"].nunique()),
            "total_state_records": int(len(df)),
            "total_canonical_rows": int(len(canonical_df)),
            "censored_row_count": int(censored_count),
            "invalid_row_count": int(invalidation_count),
            "duplicate_row_count": int(canonical_df.duplicated(subset=["row_id"]).sum()),
            "availability": {
                "ood": bool(has_ood),
                "uncertainty": bool(has_unc),
                "drift": bool(has_drift),
                "fused_risk": bool(has_fused),
                "memory": bool(has_mem),
                "temporal": bool(has_temp),
                "early_warning": bool(has_ew),
                "ground_truth": bool(has_ground_truth),
            },
        }

        return canonical_df, stats

    def create_group_aware_split(
        self,
        canonical_df: pd.DataFrame,
        train_ratio: float = 0.6,
        cal_ratio: float = 0.2,
        test_ratio: float = 0.2,
        seed: int = 42,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Enforces deterministic group-aware trajectory split (60/20/20).
        Ensures zero trajectory overlap across Train, Calibration, and Final Test splits.
        """
        assert abs((train_ratio + cal_ratio + test_ratio) - 1.0) < 1e-5, "Split ratios must sum to 1.0"

        unique_trajectories = sorted(canonical_df["trajectory_id"].unique())
        n_trajs = len(unique_trajectories)

        if n_trajs < 3:
            # Domain limitation warning: insufficient trajectories for 60/20/20
            # Fall back to returning all trajectories in train/cal with test independent
            np.random.seed(seed)
            shuffled = np.array(unique_trajectories)
            train_trajs = shuffled[:1].tolist()
            cal_trajs = shuffled[1:2].tolist()
            test_trajs = shuffled[2:].tolist() if n_trajs >= 3 else shuffled[:1].tolist()
        else:
            np.random.seed(seed)
            shuffled_trajs = np.random.permutation(unique_trajectories)

            n_train = int(np.round(n_trajs * train_ratio))
            n_cal = int(np.round(n_trajs * cal_ratio))
            if n_train + n_cal >= n_trajs:
                n_train = max(1, n_trajs - 2)
                n_cal = 1

            train_trajs = shuffled_trajs[:n_train].tolist()
            cal_trajs = shuffled_trajs[n_train : n_train + n_cal].tolist()
            test_trajs = shuffled_trajs[n_train + n_cal :].tolist()

        # Check zero trajectory overlap
        train_set, cal_set, test_set = set(train_trajs), set(cal_trajs), set(test_trajs)
        assert len(train_set.intersection(cal_set)) == 0, "Leakage Error: Train and Cal overlap!"
        assert len(train_set.intersection(test_set)) == 0, "Leakage Error: Train and Test overlap!"
        assert len(cal_set.intersection(test_set)) == 0, "Leakage Error: Cal and Test overlap!"

        train_df = canonical_df[canonical_df["trajectory_id"].isin(train_trajs)].reset_index(drop=True)
        cal_df = canonical_df[canonical_df["trajectory_id"].isin(cal_trajs)].reset_index(drop=True)
        test_df = canonical_df[canonical_df["trajectory_id"].isin(test_trajs)].reset_index(drop=True)

        manifest = {
            "seed": seed,
            "total_trajectories": n_trajs,
            "train_trajectories": train_trajs,
            "cal_trajectories": cal_trajs,
            "test_trajectories": test_trajs,
            "train_row_count": len(train_df),
            "cal_row_count": len(cal_df),
            "test_row_count": len(test_df),
            "zero_overlap_verified": True,
        }

        return train_df, cal_df, test_df, manifest
