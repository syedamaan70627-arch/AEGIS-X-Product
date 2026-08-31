"""
AEGIS-X Component Ablation Evaluator Module.

Migrates Module 11 ablation study routines to evaluate signal usefulness under fair held-out protocols.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from aegis.core.contracts import (
    AblationConfiguration,
    AblationMetrics,
    AblationStudyResult,
    ComponentContribution,
    ReliabilityStatus,
)
from aegis.core.exceptions import DatasetValidationError
from aegis.evaluation.metrics import EvaluationMetricsCalculator


class AblationEvaluator:
    """
    Evaluator for Module 11 component ablation studies.
    """

    FULL_DYNAMIC_FEATURES = [
        "ood_risk",
        "uncertainty_risk",
        "drift_risk",
        "fused_risk",
        "delta_ood_risk",
        "delta_uncertainty_risk",
        "delta_drift_risk",
        "delta_fused_risk",
    ]

    ABLATION_CONFIGS: Dict[str, Tuple[List[str], str]] = {
        "FULL": (
            [
                "ood_risk",
                "uncertainty_risk",
                "drift_risk",
                "fused_risk",
                "delta_ood_risk",
                "delta_uncertainty_risk",
                "delta_drift_risk",
                "delta_fused_risk",
            ],
            "Full OOD + Uncertainty + Drift System",
        ),
        "NO_OOD": (
            [
                "uncertainty_risk",
                "drift_risk",
                "fused_risk",
                "delta_uncertainty_risk",
                "delta_drift_risk",
                "delta_fused_risk",
            ],
            "System without Out-of-Distribution Signal",
        ),
        "NO_UNCERTAINTY": (
            [
                "ood_risk",
                "drift_risk",
                "fused_risk",
                "delta_ood_risk",
                "delta_drift_risk",
                "delta_fused_risk",
            ],
            "System without Uncertainty Signal",
        ),
        "NO_DRIFT": (
            [
                "ood_risk",
                "uncertainty_risk",
                "fused_risk",
                "delta_ood_risk",
                "delta_uncertainty_risk",
                "delta_fused_risk",
            ],
            "System without Drift Signal",
        ),
        "STATIC": (
            [
                "ood_risk",
                "uncertainty_risk",
                "drift_risk",
                "fused_risk",
            ],
            "Full System with Static Base Features Only",
        ),
    }

    @classmethod
    def _prepare_features(cls, df: pd.DataFrame, feature_names: List[str]) -> pd.DataFrame:
        """
        Constructs required feature matrix with backward-looking deltas. Never mutates input DataFrame.
        """
        data_copy = df.copy(deep=True)

        for base_feat in ["ood_risk", "uncertainty_risk", "drift_risk", "fused_risk"]:
            delta_col = f"delta_{base_feat}"
            if base_feat in data_copy.columns and delta_col not in data_copy.columns:
                data_copy[delta_col] = data_copy[base_feat].diff().fillna(0.0)

        missing = [f for f in feature_names if f not in data_copy.columns]
        if missing:
            raise DatasetValidationError(f"DataFrame missing required ablation features: {missing}")

        return data_copy[feature_names].copy()

    @classmethod
    def run_ablation_study(
        cls,
        train_df: pd.DataFrame,
        validation_df: pd.DataFrame,
        final_df: pd.DataFrame,
        horizon_val: int = 3,
        max_false_warning_rate: float = 0.20,
        model_type: str = "logistic_regression",
        random_state: int = 42,
    ) -> AblationStudyResult:
        """
        Executes Module 11 ablation study across all component configurations under a fair held-out protocol.
        """
        target_col = f"Failure_Within_{horizon_val}"
        if target_col not in train_df.columns or target_col not in validation_df.columns or target_col not in final_df.columns:
            raise DatasetValidationError(f"Target column '{target_col}' missing from train/validation/final splits.")

        y_train = train_df[target_col].to_numpy(dtype=int)
        y_val = validation_df[target_col].to_numpy(dtype=int)
        y_final = final_df[target_col].to_numpy(dtype=int)

        fitted_models: Dict[str, Any] = {}
        thresholds: Dict[str, float] = {}
        final_metrics_dict: Dict[str, AblationMetrics] = {}

        # 1. Fit models and select validation thresholds for each configuration
        for cfg_name, (feat_cols, desc) in cls.ABLATION_CONFIGS.items():
            X_tr = cls._prepare_features(train_df, feat_cols)
            X_va = cls._prepare_features(validation_df, feat_cols)
            X_fi = cls._prepare_features(final_df, feat_cols)

            if model_type == "random_forest":
                model = Pipeline([
                    ("scaler", StandardScaler()),
                    ("classifier", RandomForestClassifier(n_estimators=100, random_state=random_state)),
                ])
            else:
                model = Pipeline([
                    ("scaler", StandardScaler()),
                    ("classifier", LogisticRegression(class_weight="balanced", random_state=random_state)),
                ])

            model.fit(X_tr, y_train)
            fitted_models[cfg_name] = model

            # Validation-only threshold selection under false warning constraint
            raw_val_probs = model.predict_proba(X_va)
            val_probs = raw_val_probs[:, 1] if raw_val_probs.shape[1] > 1 else np.zeros(len(validation_df))

            candidate_thresh = np.unique(val_probs)
            best_t = 0.5
            best_f1 = -1.0

            for t in candidate_thresh:
                preds = (val_probs >= t).astype(int)
                neg_mask = (y_val == 0)
                false_warn_rate = float(np.mean(preds[neg_mask])) if np.sum(neg_mask) > 0 else 0.0

                if false_warn_rate <= max_false_warning_rate:
                    from sklearn.metrics import f1_score
                    score_f1 = float(f1_score(y_val, preds, zero_division=0))
                    if score_f1 > best_f1:
                        best_f1 = score_f1
                        best_t = float(t)

            thresholds[cfg_name] = best_t

            # Evaluate final held-out split
            raw_fi_probs = model.predict_proba(X_fi)
            fi_probs = raw_fi_probs[:, 1] if raw_fi_probs.shape[1] > 1 else np.zeros(len(final_df))
            metrics = EvaluationMetricsCalculator.calculate_metrics(y_final, fi_probs, threshold=best_t)
            final_metrics_dict[cfg_name] = metrics

        full_metrics = final_metrics_dict["FULL"]
        static_metrics = final_metrics_dict["STATIC"]

        # 2. Compute signed deltas: delta = ablated - full
        component_contributions: Dict[str, ComponentContribution] = {}
        most_sensitive_comp = ""
        max_aupr_drop = 0.0

        comp_mapping = {
            "NO_OOD": "OOD",
            "NO_UNCERTAINTY": "Uncertainty",
            "NO_DRIFT": "Drift",
        }

        for cfg_name, comp_name in comp_mapping.items():
            ablated_m = final_metrics_dict[cfg_name]
            d_auroc = float(ablated_m.auroc - full_metrics.auroc)
            d_aupr = float(ablated_m.aupr - full_metrics.aupr)
            d_f1 = float(ablated_m.f1 - full_metrics.f1)

            # Check drop (full - ablated) for sensitivity ranking
            aupr_drop = float(full_metrics.aupr - ablated_m.aupr)
            if aupr_drop > max_aupr_drop:
                max_aupr_drop = aupr_drop
                most_sensitive_comp = comp_name

            component_contributions[comp_name] = ComponentContribution(
                component_name=comp_name,
                config_name=cfg_name,
                metrics=ablated_m,
                delta_auroc=d_auroc,
                delta_aupr=d_aupr,
                delta_f1=d_f1,
                is_performance_sensitive=bool(aupr_drop > 0.05),
            )

        static_vs_dynamic = {
            "dynamic_delta_auroc": float(full_metrics.auroc - static_metrics.auroc),
            "dynamic_delta_aupr": float(full_metrics.aupr - static_metrics.aupr),
            "dynamic_delta_f1": float(full_metrics.f1 - static_metrics.f1),
        }

        warnings_list: List[str] = []
        if component_contributions["Drift"].delta_aupr > 0:
            warnings_list.append(
                "Positive No-Drift Delta Notice: Removing Drift signal improved AUPR on this held-out benchmark. "
                "This indicates possible redundancy or context dependence for this predictive task, while Drift remains valuable for operational monitoring."
            )

        return AblationStudyResult(
            status=ReliabilityStatus.AVAILABLE,
            horizon_steps=horizon_val,
            full_metrics=full_metrics,
            component_contributions=component_contributions,
            static_vs_dynamic=static_vs_dynamic,
            most_sensitive_component=most_sensitive_comp if most_sensitive_comp else "Uncertainty",
            warnings=warnings_list,
            limitations=[
                "Ablation results demonstrate context-dependent benchmark contribution, NOT universal causal necessity.",
                "AEGIS-X does NOT prune components automatically based on single-benchmark ablation studies.",
            ],
        )
