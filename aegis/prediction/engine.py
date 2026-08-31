"""
AEGIS-X Failure Predictor Engine Module.

Migrates Module 9R onset-aware failure prediction engine with validation-only thresholding
and strict fit vs inference separation.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

from aegis.core.contracts import (
    FailurePredictionEvent,
    FailurePredictionResult,
    PredictionThresholdInfo,
    ReliabilityStatus,
)
from aegis.core.exceptions import DatasetValidationError
from aegis.prediction.features import PredictionFeatureBuilder
from aegis.prediction.threshold import ValidationThresholdSelector


class FailurePredictor:
    """
    Failure Predictor Engine for Module 9R next-step onset-aware failure prediction.
    """

    def __init__(
        self,
        feature_set_type: str = "dynamic",
        model_type: str = "random_forest",
        random_state: int = 42,
    ) -> None:
        self.feature_set_type: str = feature_set_type
        self.model_type: str = model_type
        self.random_state: int = random_state

        self.scaler: StandardScaler = StandardScaler()
        self.model: Optional[Any] = None
        self.threshold_info: Optional[PredictionThresholdInfo] = None
        self.feature_names: List[str] = PredictionFeatureBuilder.FEATURE_SETS.get(feature_set_type, [])
        self.is_fitted: bool = False
        self.horizon_steps: int = 1

    def fit(
        self,
        train_df: pd.DataFrame,
        validation_df: pd.DataFrame,
        target_column: str = "Failure_Onset_Next",
        feature_set_type: Optional[str] = None,
        random_state: Optional[int] = None,
    ) -> FailurePredictionResult:
        """
        Fits prediction model on train_df and selects warning threshold on validation_df.
        """
        seed = random_state if random_state is not None else self.random_state
        if feature_set_type is not None:
            self.feature_set_type = feature_set_type

        # 1. Build features for train & validation splits
        X_train, self.feature_names = PredictionFeatureBuilder.build_features(train_df, self.feature_set_type)
        X_val, _ = PredictionFeatureBuilder.build_features(validation_df, self.feature_set_type)

        if target_column not in train_df.columns or target_column not in validation_df.columns:
            raise DatasetValidationError(f"Target column '{target_column}' missing from train/validation splits.")

        y_train = train_df[target_column].to_numpy(dtype=int)
        y_val = validation_df[target_column].to_numpy(dtype=int)

        # 2. Fit Scaler & Model on Train split
        X_train_scaled = self.scaler.fit_transform(X_train)

        if self.model_type == "gradient_boosting":
            self.model = GradientBoostingClassifier(n_estimators=100, random_state=seed)
        else:
            self.model = RandomForestClassifier(n_estimators=100, random_state=seed)

        self.model.fit(X_train_scaled, y_train)

        # 3. Validation-Only Threshold Selection
        X_val_scaled = self.scaler.transform(X_val)
        raw_val_probs = self.model.predict_proba(X_val_scaled)
        if raw_val_probs.shape[1] > 1:
            val_probs = raw_val_probs[:, 1]
        elif len(self.model.classes_) == 1 and self.model.classes_[0] == 1:
            val_probs = raw_val_probs[:, 0]
        else:
            val_probs = np.zeros(len(X_val))

        self.threshold_info = ValidationThresholdSelector.select_best_threshold(y_val, val_probs)
        self.is_fitted = True

        return FailurePredictionResult(
            status=ReliabilityStatus.AVAILABLE,
            horizon_steps=self.horizon_steps,
            selected_predictor=f"{self.model_type}_{self.feature_set_type}",
            threshold_info=self.threshold_info,
            warnings=[],
            limitations=[
                "Failure prediction models upcoming controlled degradation transitions.",
                "Threshold selection is fitted exclusively on validation splits.",
            ],
        )

    def predict(
        self,
        query_df: pd.DataFrame,
        y_true_onset: Optional[Union[pd.Series, np.ndarray, list]] = None,
    ) -> FailurePredictionResult:
        """
        Executes prediction on query DataFrame using pre-fitted scaler and threshold.
        Held-out query labels CANNOT alter or re-tune the pre-fixed threshold.
        """
        if not self.is_fitted or self.model is None or self.threshold_info is None:
            return FailurePredictionResult(
                status=ReliabilityStatus.NOT_AVAILABLE,
                horizon_steps=self.horizon_steps,
                selected_predictor=f"{self.model_type}_{self.feature_set_type}",
                warnings=["Failure prediction model is not fitted for this deployment/setup."],
                limitations=[
                    "Failure prediction requires pre-fitted degradation trajectory models.",
                    "Untrained deployments return ReliabilityStatus.NOT_AVAILABLE.",
                ],
            )

        # 1. Build features & transform using pre-fitted scaler
        X_query, _ = PredictionFeatureBuilder.build_features(query_df, self.feature_set_type)
        X_scaled = self.scaler.transform(X_query)

        # 2. Predict failure probabilities
        raw_probs = self.model.predict_proba(X_scaled)
        if raw_probs.shape[1] > 1:
            probs = raw_probs[:, 1]
        elif len(self.model.classes_) == 1 and self.model.classes_[0] == 1:
            probs = raw_probs[:, 0]
        else:
            probs = np.zeros(len(query_df))
        threshold = self.threshold_info.threshold
        warnings = (probs >= threshold)

        num_samples = len(query_df)
        events: List[FailurePredictionEvent] = []
        y_arr = np.asarray(y_true_onset) if y_true_onset is not None else None

        for i in range(num_samples):
            ev = FailurePredictionEvent(
                sample_id=i,
                predicted_failure_prob=float(probs[i]),
                is_failure_warning=bool(warnings[i]),
                threshold=threshold,
                actual_failure_onset=bool(y_arr[i]) if y_arr is not None else None,
            )
            events.append(ev)

        # Optional held-out evaluation if labels provided
        heldout_metrics: Optional[Dict[str, float]] = None
        if y_arr is not None and np.sum(y_arr) > 0:
            preds = warnings.astype(int)
            rec = float(recall_score(y_arr, preds, zero_division=0))
            prec = float(precision_score(y_arr, preds, zero_division=0))
            f1 = float(f1_score(y_arr, preds, zero_division=0))
            auc = float(roc_auc_score(y_arr, probs)) if len(np.unique(y_arr)) > 1 else 0.5

            heldout_metrics = {
                "recall": rec,
                "precision": prec,
                "f1": f1,
                "auroc": auc,
            }

        return FailurePredictionResult(
            status=ReliabilityStatus.AVAILABLE,
            horizon_steps=self.horizon_steps,
            selected_predictor=f"{self.model_type}_{self.feature_set_type}",
            threshold_info=self.threshold_info,
            predictions=events,
            aggregate_onset_warning_rate=float(np.mean(warnings)),
            mean_predicted_probability=float(np.mean(probs)),
            heldout_metrics=heldout_metrics,
            warnings=[],
            limitations=[
                "Failure prediction models upcoming controlled degradation transitions.",
                "Controlled degradation steps are synthetic trajectory steps, NOT real-world clock time.",
                "Held-out evaluation is based on small sample sizes from controlled experiments.",
            ],
        )

    def save_artifact(self, directory_path: Union[str, Path]) -> None:
        """Saves pre-fitted predictor models, scaler, and threshold metadata."""
        if not self.is_fitted or self.model is None or self.threshold_info is None:
            raise DatasetValidationError("Cannot save un-fitted FailurePredictor.")

        dir_path = Path(directory_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.scaler, dir_path / "failure_predictor_scaler.pkl")
        joblib.dump(self.model, dir_path / "failure_predictor_model.pkl")

        metadata = {
            "model_type": self.model_type,
            "feature_set_type": self.feature_set_type,
            "feature_names": self.feature_names,
            "horizon_steps": self.horizon_steps,
            "threshold_info": {
                "threshold": self.threshold_info.threshold,
                "selection_metric": self.threshold_info.selection_metric,
                "selection_split": self.threshold_info.selection_split,
                "validation_f1": self.threshold_info.validation_f1,
                "validation_recall": self.threshold_info.validation_recall,
                "validation_precision": self.threshold_info.validation_precision,
            },
        }

        with open(dir_path / "failure_prediction_config.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def load_artifact(self, directory_path: Union[str, Path]) -> "FailurePredictor":
        """Loads pre-fitted predictor models, scaler, and threshold metadata."""
        dir_path = Path(directory_path)

        scaler_path = dir_path / "failure_predictor_scaler.pkl"
        model_path = dir_path / "failure_predictor_model.pkl"
        json_path = dir_path / "failure_prediction_config.json"

        if not (scaler_path.exists() and model_path.exists() and json_path.exists()):
            raise DatasetValidationError(f"Missing required FailurePredictor artifacts in {dir_path}")

        self.scaler = joblib.load(scaler_path)
        self.model = joblib.load(model_path)

        with open(json_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        self.model_type = metadata["model_type"]
        self.feature_set_type = metadata["feature_set_type"]
        self.feature_names = metadata["feature_names"]
        self.horizon_steps = metadata.get("horizon_steps", 1)

        t_data = metadata["threshold_info"]
        self.threshold_info = PredictionThresholdInfo(
            threshold=t_data["threshold"],
            selection_metric=t_data["selection_metric"],
            selection_split=t_data["selection_split"],
            validation_f1=t_data["validation_f1"],
            validation_recall=t_data["validation_recall"],
            validation_precision=t_data["validation_precision"],
        )

        self.is_fitted = True
        return self
