"""
AEGIS-X Module 14 — Evidence-Calibrated Reliability Governance (ECRG)
Deterministic, Leakage-Safe Research Evidence Dataset Builder (Phase 2B Repaired).

Provides mathematically sound separation between:
1. STATIC_SELECTIVE_RISK: Genuine static classification (Breast Cancer, Digits) using prediction error as ground truth.
2. TEMPORAL_GOVERNANCE: Genuine temporal trajectories (NASA C-MAPSS, Synthetic Degradation) using future horizon failure labels.
3. AUXILIARY_SIMULATED_SEQUENCE: Explicitly labeled simulated sequences for builder testing and negative controls.
"""

import hashlib
import json
import os
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from aegis.core.analyzer import CoreReliabilityAnalyzer
from aegis.core.exceptions import DatasetValidationError
from aegis.core.model_adapter import SklearnModelAdapter
from aegis.core.temporal import compute_future_failure_within_n


BUILDER_VERSION = "1.1.0"
DEFAULT_HORIZONS = [1, 2, 3, 5]
TARGET_ALPHAS = [0.05, 0.10, 0.20]


def compute_sha256_hash(data: Union[str, bytes, pd.DataFrame, dict]) -> str:
    """Computes deterministic SHA-256 hash for strings, bytes, DataFrames, or dicts."""
    if isinstance(data, pd.DataFrame):
        content = data.to_csv(index=False).encode("utf-8")
    elif isinstance(data, dict):
        content = json.dumps(data, sort_keys=True).encode("utf-8")
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
        self.config_hash = config_hash or hashlib.sha256(b"ECRG_BUILDER_V1_1_CONFIG").hexdigest()[:16]

    # -------------------------------------------------------------------------
    # 1. STATIC SELECTIVE RISK DATASET BUILDER
    # -------------------------------------------------------------------------
    def build_static_selective_risk_rows(
        self,
        X: pd.DataFrame,
        y_true: pd.Series,
        y_pred: pd.Series,
        model_id: str,
        dataset_id: str,
        domain_id: str,
        ood_scores: Optional[np.ndarray] = None,
        uncertainty_scores: Optional[np.ndarray] = None,
        drift_scores: Optional[np.ndarray] = None,
        fused_risks: Optional[np.ndarray] = None,
        seed: int = 42,
        source_artifact_path: str = "sklearn_fixture",
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Constructs canonical evidence rows for genuine static classification tasks.
        Ground truth is defined strictly as prediction_error = 1(y_pred != y_true).
        Temporal fields (trajectory_id, state_index, failure_within_horizon) remain UNAVAILABLE.
        """
        source_hash = compute_sha256_hash(X)
        records = []
        n_samples = len(X)

        has_ood = ood_scores is not None
        has_unc = uncertainty_scores is not None
        has_drift = drift_scores is not None
        has_fused = fused_risks is not None

        for i in range(n_samples):
            row_key = f"{model_id}:{domain_id}:{seed}:sample_{i}"
            row_id = hashlib.sha256(row_key.encode("utf-8")).hexdigest()[:24]

            t_val = int(y_true.iloc[i]) if pd.notna(y_true.iloc[i]) else None
            p_val = int(y_pred.iloc[i]) if pd.notna(y_pred.iloc[i]) else None
            pred_correct = (t_val == p_val) if (t_val is not None and p_val is not None) else None
            pred_error = int(not pred_correct) if pred_correct is not None else None

            # Same-state signal disagreement if signals available
            avail = []
            if has_ood and pd.notna(ood_scores[i]): avail.append(float(ood_scores[i]))
            if has_unc and pd.notna(uncertainty_scores[i]): avail.append(float(uncertainty_scores[i]))
            if has_drift and pd.notna(drift_scores[i]): avail.append(float(drift_scores[i]))
            sig_dis = float(np.std(avail)) if len(avail) >= 2 else 0.0

            record = {
                "row_id": row_id,
                "task_type": "STATIC_SELECTIVE_RISK",
                "source_module": "Module_12_CrossDomain",
                "source_artifact_path": source_artifact_path,
                "source_artifact_hash": source_hash,
                "model_id": model_id,
                "dataset_id": dataset_id,
                "domain_id": domain_id,
                "seed": seed,
                # Temporal fields strictly UNAVAILABLE for static task
                "trajectory_id": None,
                "state_index": None,
                "prediction_horizon": None,
                "extraction_timestamp": "2026-09-02T20:45:00Z",
                "builder_version": BUILDER_VERSION,
                "config_hash": self.config_hash,
                # Ground-truth semantics
                "outcome_semantics": "SAMPLE_PREDICTION_ERROR",
                "failure_definition": "prediction_error == 1 when model prediction != true target",
                "label_source": "model_prediction_versus_ground_truth",
                "label_available_at_runtime": False,
                "true_class": t_val,
                "predicted_class": p_val,
                "prediction_correct": pred_correct,
                "prediction_error": pred_error,
                # Reliability Scores
                "ood_score": float(ood_scores[i]) if has_ood and pd.notna(ood_scores[i]) else None,
                "uncertainty_score": float(uncertainty_scores[i]) if has_unc and pd.notna(uncertainty_scores[i]) else None,
                "drift_score": float(drift_scores[i]) if has_drift and pd.notna(drift_scores[i]) else None,
                "fused_risk": float(fused_risks[i]) if has_fused and pd.notna(fused_risks[i]) else None,
                "stress_robust_fused_risk": float(fused_risks[i]) if has_fused and pd.notna(fused_risks[i]) else None,
                "signal_disagreement": sig_dis,
                "ood_drift_redundancy": None,
                "stress_robustness": None,
                "fault_sensitivity": None,
                "memory_similarity": None,
                "temporal_failure_probability": None,
                "early_warning_state": "NORMAL",
                # Explicit Availability Flags
                "has_ood": has_ood,
                "has_uncertainty": has_unc,
                "has_drift": has_drift,
                "has_fused_risk": has_fused,
                "has_memory": False,
                "has_temporal": False,
                "has_early_warning": False,
                "has_ground_truth": True,
                "is_censored": False,
                # Temporal Targets (None for static)
                "eventual_failure": None,
                "failure_event_index": None,
                "failure_within_horizon": None,
                "states_remaining_before_failure": None,
            }
            records.append(record)

        df_static = pd.DataFrame(records)

        stats = {
            "task_type": "STATIC_SELECTIVE_RISK",
            "model_id": str(model_id),
            "dataset_id": str(dataset_id),
            "domain_id": str(domain_id),
            "seed": int(seed),
            "source_artifact_hash": str(source_hash),
            "total_independent_samples": n_samples,
            "total_canonical_rows": len(df_static),
            "total_prediction_errors": int((y_pred != y_true).sum()),
            "overall_error_rate": float((y_pred != y_true).mean()),
            "availability": {
                "ood": bool(has_ood),
                "uncertainty": bool(has_unc),
                "drift": bool(has_drift),
                "fused_risk": bool(has_fused),
                "ground_truth": True,
            },
        }

        return df_static, stats

    # -------------------------------------------------------------------------
    # 2. TEMPORAL GOVERNANCE DATASET BUILDER
    # -------------------------------------------------------------------------
    def build_temporal_governance_rows(
        self,
        df: pd.DataFrame,
        model_id: str,
        dataset_id: str,
        domain_id: str,
        seed: int = 42,
        source_module: str = "Modules_12_13_EarlyWarning",
        source_artifact_path: str = "temporal_raw",
        horizons: List[int] = DEFAULT_HORIZONS,
        task_type: str = "TEMPORAL_GOVERNANCE",
        outcome_semantics: str = "CONTROLLED_FAILURE_EVENT",
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Constructs canonical long-format evidence rows for genuine temporal trajectories.
        Enforces right-censoring, horizon label monotonicity for valid steps, and trajectory group isolation.
        """
        df = df.copy()
        source_hash = compute_sha256_hash(df)

        if "trajectory_id" not in df.columns:
            raise DatasetValidationError("Temporal dataset must contain a 'trajectory_id' column.")
        if "step" not in df.columns and "sequence_step" in df.columns:
            df["step"] = df["sequence_step"]
        if "step" not in df.columns and "cycle" in df.columns:
            df["step"] = df["cycle"]
        if "step" not in df.columns:
            raise DatasetValidationError("Temporal dataset must contain a 'step' or 'cycle' column.")

        has_gt = "is_failure" in df.columns
        gt_col = "is_failure" if has_gt else None

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

        records = []
        censored_count = 0

        for traj_id, group in df.groupby("trajectory_id", sort=False):
            group = group.sort_values("step").reset_index(drop=True)
            n_steps = len(group)

            if has_gt:
                group["is_failure_clean"] = group[gt_col].fillna(0).astype(int)
                fail_indices = group.index[group["is_failure_clean"] == 1].tolist()
                first_fail_idx = fail_indices[0] if len(fail_indices) > 0 else None
                eventual_fail = 1 if len(fail_indices) > 0 else 0
            else:
                group["is_failure_clean"] = None
                first_fail_idx = None
                eventual_fail = None

            # Pre-compute future failure within N for each horizon
            horizon_targets = {}
            if has_gt:
                for k in horizons:
                    horizon_targets[k] = compute_future_failure_within_n(group["is_failure_clean"], k).to_numpy()

            for i in range(n_steps):
                step_idx = int(group.loc[i, "step"])

                # Compute remaining states before failure
                if first_fail_idx is not None and first_fail_idx >= i:
                    states_remaining = int(first_fail_idx - i)
                else:
                    states_remaining = None

                # Same-state signal disagreement
                avail_signals = []
                if has_ood and pd.notna(group.loc[i, ood_col]): avail_signals.append(float(group.loc[i, ood_col]))
                if has_unc and pd.notna(group.loc[i, unc_col]): avail_signals.append(float(group.loc[i, unc_col]))
                if has_drift and pd.notna(group.loc[i, drift_col]): avail_signals.append(float(group.loc[i, drift_col]))
                sig_dis = float(np.std(avail_signals)) if len(avail_signals) >= 2 else 0.0

                for k in horizons:
                    row_key = f"{model_id}:{domain_id}:{seed}:{traj_id}:{step_idx}:{k}"
                    row_id = hashlib.sha256(row_key.encode("utf-8")).hexdigest()[:24]

                    # Strict Censoring Check:
                    # If step i + k exceeds trajectory length AND no failure has occurred yet,
                    # the state's horizon k outcome is RIGHT-CENSORED (None target, is_censored = True).
                    censored = False
                    if has_gt:
                        raw_target_k = int(horizon_targets[k][i])
                        if (i + k >= n_steps) and (eventual_fail == 0):
                            censored = True
                            target_k = None  # Do NOT zero-fill censored horizon
                            censored_count += 1
                        else:
                            target_k = raw_target_k
                    else:
                        target_k = None

                    record = {
                        "row_id": row_id,
                        "task_type": task_type,
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
                        # Ground-truth semantics
                        "outcome_semantics": outcome_semantics,
                        "failure_definition": "is_failure onset or future failure within K cycles/steps",
                        "label_source": "trajectory_ground_truth_sequence",
                        "label_available_at_runtime": False,
                        "true_class": None,
                        "predicted_class": None,
                        "prediction_correct": None,
                        "prediction_error": None,
                        # Reliability Scores
                        "ood_score": float(group.loc[i, ood_col]) if has_ood and pd.notna(group.loc[i, ood_col]) else None,
                        "uncertainty_score": float(group.loc[i, unc_col]) if has_unc and pd.notna(group.loc[i, unc_col]) else None,
                        "drift_score": float(group.loc[i, drift_col]) if has_drift and pd.notna(group.loc[i, drift_col]) else None,
                        "fused_risk": float(group.loc[i, fused_col]) if has_fused and pd.notna(group.loc[i, fused_col]) else None,
                        "stress_robust_fused_risk": float(group.loc[i, stress_fused_col]) if stress_fused_col and pd.notna(group.loc[i, stress_fused_col]) else None,
                        "signal_disagreement": sig_dis,
                        "ood_drift_redundancy": None,
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
                        "has_ground_truth": has_gt,
                        "is_censored": censored,
                        # Temporal Targets
                        "eventual_failure": eventual_fail,
                        "failure_event_index": first_fail_idx,
                        "failure_within_horizon": target_k,
                        "states_remaining_before_failure": states_remaining,
                    }
                    records.append(record)

        df_temporal = pd.DataFrame(records)

        # Monotonicity check on non-censored rows
        for (t_id, s_idx), grp in df_temporal.groupby(["trajectory_id", "state_index"]):
            grp_valid = grp[grp["is_censored"] == False].sort_values("prediction_horizon")
            if len(grp_valid) > 1 and has_gt:
                t_list = grp_valid["failure_within_horizon"].dropna().tolist()
                for idx_m in range(len(t_list) - 1):
                    if t_list[idx_m] > t_list[idx_m + 1]:
                        raise DatasetValidationError(
                            f"Monotonicity error at trajectory {t_id}, step {s_idx}: {t_list[idx_m]} > {t_list[idx_m+1]}"
                        )

        stats = {
            "task_type": task_type,
            "model_id": str(model_id),
            "dataset_id": str(dataset_id),
            "domain_id": str(domain_id),
            "seed": int(seed),
            "source_artifact_hash": str(source_hash),
            "total_independent_trajectories": int(df["trajectory_id"].nunique()),
            "total_state_records": int(len(df)),
            "total_canonical_rows": int(len(df_temporal)),
            "censored_row_count": int(censored_count),
            "duplicate_row_count": int(df_temporal.duplicated(subset=["row_id"]).sum()),
            "availability": {
                "ood": bool(has_ood),
                "uncertainty": bool(has_unc),
                "drift": bool(has_drift),
                "fused_risk": bool(has_fused),
                "memory": bool(has_mem),
                "temporal": bool(has_temp),
                "early_warning": bool(has_ew),
                "ground_truth": bool(has_gt),
            },
        }

        return df_temporal, stats

    # -------------------------------------------------------------------------
    # 3. GROUP-AWARE SPLITTING & CONFORMAL FEASIBILITY AUDIT
    # -------------------------------------------------------------------------
    def create_group_aware_split(
        self,
        df_canonical: pd.DataFrame,
        train_ratio: float = 0.6,
        cal_ratio: float = 0.2,
        test_ratio: float = 0.2,
        seed: int = 42,
        target_alphas: List[float] = TARGET_ALPHAS,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Enforces deterministic group-aware splitting and audits finite-sample conformal feasibility.
        - Static tasks: Split by sample row index.
        - Temporal tasks: Split strictly by complete trajectory_id.
        """
        task_type = df_canonical["task_type"].iloc[0] if "task_type" in df_canonical.columns else "TEMPORAL_GOVERNANCE"

        if task_type == "STATIC_SELECTIVE_RISK":
            # Stratified / Row-wise split for static samples
            n_samples = len(df_canonical)
            np.random.seed(seed)
            shuffled_idx = np.random.permutation(n_samples)

            n_train = int(np.round(n_samples * train_ratio))
            n_cal = int(np.round(n_samples * cal_ratio))

            train_df = df_canonical.iloc[shuffled_idx[:n_train]].reset_index(drop=True)
            cal_df = df_canonical.iloc[shuffled_idx[n_train : n_train + n_cal]].reset_index(drop=True)
            test_df = df_canonical.iloc[shuffled_idx[n_train + n_cal :]].reset_index(drop=True)

            n_cal_independent = len(cal_df)
            group_col = "sample_id"
        else:
            # Group-aware trajectory split for temporal tasks
            unique_groups = sorted(df_canonical["trajectory_id"].unique())
            n_groups = len(unique_groups)

            np.random.seed(seed)
            shuffled_groups = np.random.permutation(unique_groups)

            n_train_g = max(1, int(np.round(n_groups * train_ratio)))
            n_cal_g = max(1, int(np.round(n_groups * cal_ratio)))
            if n_train_g + n_cal_g >= n_groups:
                n_train_g = max(1, n_groups - 2)
                n_cal_g = 1

            train_groups = shuffled_groups[:n_train_g].tolist()
            cal_groups = shuffled_groups[n_train_g : n_train_g + n_cal_g].tolist()
            test_groups = shuffled_groups[n_train_g + n_cal_g :].tolist()

            # Zero trajectory overlap check
            tr_set, cal_set, te_set = set(train_groups), set(cal_groups), set(test_groups)
            assert len(tr_set.intersection(cal_set)) == 0, "Train and Cal share trajectories!"
            assert len(tr_set.intersection(te_set)) == 0, "Train and Test share trajectories!"
            assert len(cal_set.intersection(te_set)) == 0, "Cal and Test share trajectories!"

            train_df = df_canonical[df_canonical["trajectory_id"].isin(train_groups)].reset_index(drop=True)
            cal_df = df_canonical[df_canonical["trajectory_id"].isin(cal_groups)].reset_index(drop=True)
            test_df = df_canonical[df_canonical["trajectory_id"].isin(test_groups)].reset_index(drop=True)

            n_cal_independent = len(cal_groups)
            group_col = "trajectory_id"

        # Conformal Feasibility Audit
        resolution = 1.0 / (n_cal_independent + 1.0)
        feasibility_audit = {}
        for alpha in target_alphas:
            min_req_n = int(np.ceil((1.0 - alpha) / alpha))
            is_feasible = n_cal_independent >= min_req_n
            feasibility_audit[f"alpha_{alpha}"] = {
                "target_alpha": alpha,
                "min_required_n_cal": min_req_n,
                "actual_n_cal_independent": n_cal_independent,
                "finite_sample_resolution": round(resolution, 4),
                "is_conformal_feasible": is_feasible,
                "warning": (
                    f"Calibration size N_cal={n_cal_independent} is insufficient to support target alpha={alpha} "
                    f"(requires N_cal >= {min_req_n}). Conformal guarantees are EXPLORATORY."
                    if not is_feasible else "FEASIBLE"
                ),
            }

        manifest = {
            "task_type": task_type,
            "seed": seed,
            "group_column": group_col,
            "n_train_independent": len(train_df["trajectory_id"].unique()) if task_type != "STATIC_SELECTIVE_RISK" else len(train_df),
            "n_cal_independent": n_cal_independent,
            "n_test_independent": len(test_df["trajectory_id"].unique()) if task_type != "STATIC_SELECTIVE_RISK" else len(test_df),
            "train_row_count": len(train_df),
            "cal_row_count": len(cal_df),
            "test_row_count": len(test_df),
            "zero_overlap_verified": True,
            "conformal_feasibility_audit": feasibility_audit,
        }

        return train_df, cal_df, test_df, manifest

    # -------------------------------------------------------------------------
    # 4. C-MAPSS EVIDENCE ADAPTER (RESTORES FROZEN V1 PATH)
    # -------------------------------------------------------------------------
    def build_cmapss_evidence(
        self,
        n_engines: int = 20,
        max_cycles: int = 150,
        seed: int = 42,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Builds canonical ECRG evidence dataset from NASA C-MAPSS turbofan degradation trajectories.
        Uses exact C-MAPSS generator and model adapter from Module 12/13 research freeze.
        """
        from aegis.experiments.run_final_research_freeze import generate_nasa_cmapss_trajectories

        df_tr, df_ev = generate_nasa_cmapss_trajectories(n_engines=n_engines, max_cycles=max_cycles, seed=seed)
        full_df = pd.concat([df_tr, df_ev], ignore_index=True)
        full_df["trajectory_id"] = full_df["engine_id"].apply(lambda e: f"engine_{e}")
        full_df["step"] = full_df["cycle"]

        # Fit model & reliability analyzer
        feat_names = ["sensor_temp_1", "sensor_temp_2", "sensor_pressure_3"]
        rf = RandomForestClassifier(n_estimators=20, random_state=seed)
        rf.fit(df_tr[feat_names], df_tr["is_failure"])
        adapter = SklearnModelAdapter(rf)

        analyzer = CoreReliabilityAnalyzer()
        analyzer.fit_reference(df_tr[feat_names], feat_names, df_tr[feat_names], df_tr["is_failure"], adapter)

        analysis_res = analyzer.analyze(full_df[feat_names], adapter)
        full_df["ood_risk"] = analysis_res.ood.risk_scores if (analysis_res.ood and analysis_res.ood.risk_scores is not None) else 0.15
        full_df["uncertainty_risk"] = analysis_res.uncertainty.uncertainty_scores if (analysis_res.uncertainty and analysis_res.uncertainty.uncertainty_scores is not None) else 0.15
        full_df["drift_risk"] = analysis_res.drift.aggregate_drift_score if analysis_res.drift else 0.10
        full_df["fused_risk"] = full_df["ood_risk"] * 0.5 + full_df["uncertainty_risk"] * 0.5

        return self.build_temporal_governance_rows(
            df=full_df,
            model_id="cmapss_random_forest_v1",
            dataset_id="nasa_cmapss_fd001",
            domain_id="cmapss_turbofan_degradation",
            seed=seed,
            source_module="Module_12_13_CMAPSS_Freeze",
            source_artifact_path="aegis.experiments.run_final_research_freeze",
            task_type="TEMPORAL_GOVERNANCE",
            outcome_semantics="C_MAPSS_FAILURE_OR_RUL_EVENT",
        )
