"""
AEGIS-X Early Warning Engine Module.

Migrates Module 10 Dynamic Multi-Signal temporal early warning engine with validation-only thresholding
and trajectory lead time evaluation.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

from aegis.core.contracts import (
    EarlyWarningEvaluation,
    ReliabilityStatus,
    WarningHorizon,
    WarningResult,
)
from aegis.core.exceptions import DatasetValidationError
from aegis.warning.features import EarlyWarningFeatureBuilder
from aegis.warning.horizon import EarlyWarningHorizonEvaluator


class EarlyWarningEngine:
    """
    Early Warning Engine for Module 10 multi-state temporal warning and lead evaluation.
    """

    def __init__(self, horizon_val: int = 3, random_state: int = 42) -> None:
        self.horizon: WarningHorizon = WarningHorizon(value=horizon_val, unit="controlled_degradation_states")
        self.random_state: int = random_state

        self.scaler: StandardScaler = StandardScaler()
        self.model: Optional[RandomForestClassifier] = None
        self.warning_threshold: float = 0.46
        self.feature_names: List[str] = EarlyWarningFeatureBuilder.DYNAMIC_MULTI_SIGNAL_FEATURES
        self.is_fitted: bool = False

    def fit(
        self,
        train_df: pd.DataFrame,
        validation_df: pd.DataFrame,
        target_column: Optional[str] = None,
        max_false_warning_rate: float = 0.20,
        random_state: Optional[int] = None,
    ) -> EarlyWarningEvaluation:
        """
        Fits warning model on train_df and selects warning threshold on validation_df under false-warning cap.
        """
        seed = random_state if random_state is not None else self.random_state
        target_col = target_column if target_column else f"Failure_Within_{self.horizon.value}"

        X_train, self.feature_names = EarlyWarningFeatureBuilder.build_features(train_df)
        X_val, _ = EarlyWarningFeatureBuilder.build_features(validation_df)

        if target_col not in train_df.columns or target_col not in validation_df.columns:
            raise DatasetValidationError(f"Target column '{target_col}' missing from train/validation splits.")

        y_train = train_df[target_col].to_numpy(dtype=int)
        y_val = validation_df[target_col].to_numpy(dtype=int)

        # 1. Fit Scaler & Model on Train split
        X_train_scaled = self.scaler.fit_transform(X_train)
        self.model = RandomForestClassifier(n_estimators=100, random_state=seed)
        self.model.fit(X_train_scaled, y_train)

        # 2. Validation-Only Threshold Selection (under max_false_warning_rate constraint)
        X_val_scaled = self.scaler.transform(X_val)
        raw_val_probs = self.model.predict_proba(X_val_scaled)
        val_probs = raw_val_probs[:, 1] if raw_val_probs.shape[1] > 1 else np.zeros(len(validation_df))

        candidate_thresholds = np.unique(val_probs)
        best_t = 0.46
        best_f1 = -1.0

        for t in candidate_thresholds:
            preds = (val_probs >= t).astype(int)
            neg_mask = (y_val == 0)
            false_warn_rate = float(np.mean(preds[neg_mask])) if np.sum(neg_mask) > 0 else 0.0

            if false_warn_rate <= max_false_warning_rate:
                score_f1 = float(f1_score(y_val, preds, zero_division=0))
                if score_f1 > best_f1:
                    best_f1 = score_f1
                    best_t = float(t)

        self.warning_threshold = best_t
        self.is_fitted = True

        # State-level validation metrics
        val_preds = (val_probs >= self.warning_threshold).astype(int)
        state_metrics = {
            "auroc": float(roc_auc_score(y_val, val_probs)) if len(np.unique(y_val)) > 1 else 0.5,
            "aupr": float(average_precision_score(y_val, val_probs)) if len(np.unique(y_val)) > 1 else 0.5,
            "recall": float(recall_score(y_val, val_preds, zero_division=0)),
            "precision": float(precision_score(y_val, val_preds, zero_division=0)),
            "f1": float(f1_score(y_val, val_preds, zero_division=0)),
        }

        # Trajectory-level validation evaluation
        val_df_copy = validation_df.copy(deep=True)
        val_df_copy["warning_probability"] = val_probs
        traj_metrics, traj_results = EarlyWarningHorizonEvaluator.evaluate_trajectories(
            val_df_copy, horizon_val=self.horizon.value, threshold=self.warning_threshold
        )

        return EarlyWarningEvaluation(
            status=ReliabilityStatus.AVAILABLE,
            selected_horizon=self.horizon,
            warning_threshold=self.warning_threshold,
            state_level_metrics=state_metrics,
            trajectory_level_metrics=traj_metrics,
            trajectory_results=traj_results,
            warnings=[],
            limitations=[
                "Warning horizon is measured in controlled degradation states, NOT real-world clock time.",
                "Threshold selection is constrained to validation data false-warning caps.",
            ],
        )

    def predict_warning(self, query_df: pd.DataFrame) -> WarningResult:
        """
        Executes operational warning query using pre-fitted scaler and threshold.
        Never mutates state or re-tunes threshold during inference.
        """
        if not self.is_fitted or self.model is None:
            return WarningResult(
                status=ReliabilityStatus.NOT_AVAILABLE,
                warning_score=0.0,
                is_warning_triggered=False,
                threshold=self.warning_threshold,
                horizon=self.horizon,
                warnings=["Early Warning engine is not fitted for this deployment/setup."],
                limitations=[
                    "Early Warning requires pre-fitted degradation trajectory models.",
                    "Untrained deployments return ReliabilityStatus.NOT_AVAILABLE.",
                ],
            )

        X_query, _ = EarlyWarningFeatureBuilder.build_features(query_df)
        X_scaled = self.scaler.transform(X_query)

        raw_probs = self.model.predict_proba(X_scaled)
        probs = raw_probs[:, 1] if raw_probs.shape[1] > 1 else np.zeros(len(query_df))

        mean_prob = float(np.mean(probs))
        triggered = bool(mean_prob >= self.warning_threshold)

        signals_summary = {
            "mean_warning_probability": mean_prob,
            "max_warning_probability": float(np.max(probs)),
        }

        return WarningResult(
            status=ReliabilityStatus.AVAILABLE,
            warning_score=mean_prob,
            is_warning_triggered=triggered,
            threshold=self.warning_threshold,
            horizon=self.horizon,
            signals=signals_summary,
            warnings=[],
            limitations=[
                "Warning horizon unit is controlled_degradation_states, NOT real-world clock time.",
                "Non-failing trajectories in historical held-out splits produced false warnings.",
            ],
        )

    def evaluate_trajectories(self, evaluation_df: pd.DataFrame) -> EarlyWarningEvaluation:
        """
        Evaluates full held-out trajectory lead times and false warning rates.
        Held-out labels CANNOT alter or re-tune the pre-fixed threshold.
        """
        if not self.is_fitted or self.model is None:
            raise DatasetValidationError("Cannot evaluate trajectories with an un-fitted EarlyWarningEngine.")

        eval_copy = evaluation_df.copy(deep=True)
        X_eval, _ = EarlyWarningFeatureBuilder.build_features(eval_copy)
        X_scaled = self.scaler.transform(X_eval)

        raw_probs = self.model.predict_proba(X_scaled)
        eval_copy["warning_probability"] = raw_probs[:, 1] if raw_probs.shape[1] > 1 else np.zeros(len(eval_copy))

        traj_metrics, traj_results = EarlyWarningHorizonEvaluator.evaluate_trajectories(
            eval_copy, horizon_val=self.horizon.value, threshold=self.warning_threshold
        )

        state_metrics: Dict[str, float] = {}
        target_col = f"Failure_Within_{self.horizon.value}"
        if target_col in eval_copy.columns:
            y_eval = eval_copy[target_col].to_numpy(dtype=int)
            eval_probs = eval_copy["warning_probability"].to_numpy()
            eval_preds = (eval_probs >= self.warning_threshold).astype(int)

            state_metrics = {
                "auroc": float(roc_auc_score(y_eval, eval_probs)) if len(np.unique(y_eval)) > 1 else 0.5,
                "aupr": float(average_precision_score(y_eval, eval_probs)) if len(np.unique(y_eval)) > 1 else 0.5,
                "recall": float(recall_score(y_eval, eval_preds, zero_division=0)),
                "precision": float(precision_score(y_eval, eval_preds, zero_division=0)),
                "f1": float(f1_score(y_eval, eval_preds, zero_division=0)),
            }

        warnings_list: List[str] = []
        if traj_metrics.get("false_trajectory_warning_rate", 0.0) > 0.5:
            warnings_list.append(
                "False Trajectory Warning Alert: Non-failing trajectory in held-out evaluation triggered a warning (100% false warning rate on non-failing sample)."
            )

        return EarlyWarningEvaluation(
            status=ReliabilityStatus.AVAILABLE,
            selected_horizon=self.horizon,
            warning_threshold=self.warning_threshold,
            state_level_metrics=state_metrics,
            trajectory_level_metrics=traj_metrics,
            trajectory_results=traj_results,
            warnings=warnings_list,
            limitations=[
                "Lead time is measured in controlled degradation states, NOT real-world clock time.",
                "Historical trajectory evaluation demonstrated 100% coverage on failing trajectories, but 100% false warning rate on the single non-failing held-out sample.",
            ],
        )

    def save_artifact(self, directory_path: Union[str, Path]) -> None:
        """Saves warning engine models, scaler, and configuration metadata."""
        if not self.is_fitted or self.model is None:
            raise DatasetValidationError("Cannot save un-fitted EarlyWarningEngine.")

        dir_path = Path(directory_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.scaler, dir_path / "early_warning_scaler.pkl")
        joblib.dump(self.model, dir_path / "early_warning_model_h3.pkl")

        metadata = {
            "selected_horizon": self.horizon.value,
            "lead_time_unit": self.horizon.unit,
            "warning_threshold": self.warning_threshold,
            "feature_names": self.feature_names,
        }

        with open(dir_path / "early_warning_config.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def load_artifact(self, directory_path: Union[str, Path]) -> "EarlyWarningEngine":
        """Loads warning engine models, scaler, and configuration metadata."""
        dir_path = Path(directory_path)

        scaler_path = dir_path / "early_warning_scaler.pkl"
        model_path = dir_path / "early_warning_model_h3.pkl"
        json_path = dir_path / "early_warning_config.json"

        if not (scaler_path.exists() and model_path.exists() and json_path.exists()):
            raise DatasetValidationError(f"Missing required EarlyWarningEngine artifacts in {dir_path}")

        self.scaler = joblib.load(scaler_path)
        self.model = joblib.load(model_path)

        with open(json_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        self.horizon = WarningHorizon(value=metadata["selected_horizon"], unit=metadata["lead_time_unit"])
        self.warning_threshold = metadata["warning_threshold"]
        self.feature_names = metadata["feature_names"]

        self.is_fitted = True
        return self
