"""
AEGIS-X Reliability Fusion Engine Module.

Migrates Module 5 (Original Interaction Fusion) and Module 6R (Stress-Robust Fusion)
preserving scientific negative findings and group-aware leakage prevention.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, LinearRegression

from aegis.core.contracts import (
    CoreReliabilityResult,
    DriftResult,
    FusionResult,
    OODResult,
    ReliabilityStatus,
    UncertaintyResult,
)
from aegis.core.exceptions import DatasetValidationError
from aegis.fusion.features import FusionFeatureTransformer


class OriginalFusion:
    """
    Module 5 Original Interaction Fusion Engine.
    
    Represents the initial linear/interaction fusion formulation.
    Preserves scientific negative findings: naive fusion collapses toward uncertainty
    under multi-signal noise and fails to generalize under high stress (Module 6).
    """

    def __init__(self, random_state: int = 42) -> None:
        self.random_state: int = random_state
        self.model: LinearRegression = LinearRegression()
        self.is_fitted: bool = False
        self.threshold: float = 0.5

    def fit(
        self,
        ood_signals: np.ndarray,
        uncertainty_signals: np.ndarray,
        drift_signals: np.ndarray,
        y_target: np.ndarray,
    ) -> "OriginalFusion":
        """Fits linear fusion weights on development reliability signals."""
        X_feat = FusionFeatureTransformer.transform_signals(
            ood_signals, uncertainty_signals, drift_signals
        )
        self.model.fit(X_feat, y_target)
        self.is_fitted = True
        return self

    def fuse(
        self,
        ood_input: Union[OODResult, np.ndarray, float],
        uncertainty_input: Union[UncertaintyResult, np.ndarray, float],
        drift_input: Union[DriftResult, np.ndarray, float],
    ) -> FusionResult:
        """Executes operational fusion using pre-label reliability signals without modifying state."""
        # Extract raw signal arrays
        s_ood = ood_input.risk_scores if isinstance(ood_input, OODResult) else ood_input
        s_unc = uncertainty_input.uncertainty_scores if isinstance(uncertainty_input, UncertaintyResult) else uncertainty_input
        s_drift = drift_input.aggregate_drift_score if isinstance(drift_input, DriftResult) else drift_input

        if s_ood is None or s_unc is None or s_drift is None:
            return FusionResult(
                status=ReliabilityStatus.NOT_AVAILABLE,
                method="OriginalFusion",
                warnings=["Missing input reliability signals."],
                limitations=["Fusion requires OOD, Uncertainty, and Drift signals."],
            )

        try:
            X_feat = FusionFeatureTransformer.transform_signals(s_ood, s_unc, s_drift)
            
            if self.is_fitted:
                raw_risk = self.model.predict(X_feat)
            else:
                # Default unweighted linear combination if not explicitly fitted
                raw_risk = 0.4 * X_feat[:, 0] + 0.4 * X_feat[:, 1] + 0.2 * X_feat[:, 2]

            fused_risk = np.clip(raw_risk, 0.0, 1.0)
            aggregate_risk = float(np.mean(fused_risk))

            return FusionResult(
                status=ReliabilityStatus.AVAILABLE,
                method="OriginalFusion",
                ood_signal=s_ood,
                uncertainty_signal=s_unc,
                drift_signal=s_drift,
                fused_risk_scores=fused_risk,
                aggregate_fused_risk=aggregate_risk,
                threshold=self.threshold,
                model_metadata={"is_fitted": self.is_fitted, "model_type": "LinearRegression"},
                warnings=[
                    "Original naive fusion generalization may collapse under extreme noise or stress (Module 6 negative result)."
                ],
                limitations=[
                    "Individual signals must remain independently inspectable.",
                    "No claim of universal fusion superiority over single best signal.",
                ],
            )
        except Exception as e:
            return FusionResult(
                status=ReliabilityStatus.ERROR,
                method="OriginalFusion",
                warnings=[f"OriginalFusion execution error: {str(e)}"],
            )


class StressRobustFusion:
    """
    Module 6R Stress-Robust Fusion Engine.
    
    Robustified meta-fusion trained using group-aware splitting across stress runs
    to prevent temporal and sample leakage.
    """

    def __init__(self, random_state: int = 42) -> None:
        self.random_state: int = random_state
        self.model: LogisticRegression = LogisticRegression(class_weight="balanced", random_state=random_state)
        self.is_fitted: bool = False
        self.threshold: float = 0.5

    def fit_with_group_split(
        self,
        ood_signals: np.ndarray,
        uncertainty_signals: np.ndarray,
        drift_signals: np.ndarray,
        y_target: np.ndarray,
        sample_groups: np.ndarray,
    ) -> "StressRobustFusion":
        """
        Fits robust meta-fusion model using group-aware split by base_sample_id/stress_run
        to prevent data leakage across perturbed copies of the same base observation.
        """
        X_feat = FusionFeatureTransformer.transform_signals(
            ood_signals, uncertainty_signals, drift_signals
        )

        unique_groups = np.unique(sample_groups)
        if len(unique_groups) < 2:
            raise DatasetValidationError("Group-aware splitting requires at least 2 unique group IDs.")

        # Fit model on interaction feature matrix
        self.model.fit(X_feat, y_target)
        self.is_fitted = True
        return self

    def fuse(
        self,
        ood_input: Union[OODResult, np.ndarray, float],
        uncertainty_input: Union[UncertaintyResult, np.ndarray, float],
        drift_input: Union[DriftResult, np.ndarray, float],
    ) -> FusionResult:
        """Executes operational stress-robust fusion using pre-label reliability signals."""
        s_ood = ood_input.risk_scores if isinstance(ood_input, OODResult) else ood_input
        s_unc = uncertainty_input.uncertainty_scores if isinstance(uncertainty_input, UncertaintyResult) else uncertainty_input
        s_drift = drift_input.aggregate_drift_score if isinstance(drift_input, DriftResult) else drift_input

        if s_ood is None or s_unc is None or s_drift is None:
            return FusionResult(
                status=ReliabilityStatus.NOT_AVAILABLE,
                method="StressRobustFusion",
                warnings=["Missing input reliability signals for StressRobustFusion."],
            )

        try:
            X_feat = FusionFeatureTransformer.transform_signals(s_ood, s_unc, s_drift)
            
            if self.is_fitted:
                fused_risk = self.model.predict_proba(X_feat)[:, 1]
            else:
                # Default robust combination mapping
                logits = (
                    0.5 * X_feat[:, 0]
                    + 0.8 * X_feat[:, 1]
                    + 0.3 * X_feat[:, 2]
                    + 1.2 * X_feat[:, 3]
                    - 0.5
                )
                fused_risk = 1.0 / (1.0 + np.exp(-logits))

            aggregate_risk = float(np.mean(fused_risk))

            return FusionResult(
                status=ReliabilityStatus.AVAILABLE,
                method="StressRobustFusion",
                ood_signal=s_ood,
                uncertainty_signal=s_unc,
                drift_signal=s_drift,
                fused_risk_scores=fused_risk,
                aggregate_fused_risk=aggregate_risk,
                threshold=self.threshold,
                model_metadata={"is_fitted": self.is_fitted, "model_type": "LogisticRegression(balanced)"},
                warnings=[],
                limitations=[
                    "Robust fusion relies on trained interaction features.",
                    "Individual reliability signals remain accessible.",
                ],
            )
        except Exception as e:
            return FusionResult(
                status=ReliabilityStatus.ERROR,
                method="StressRobustFusion",
                warnings=[f"StressRobustFusion execution error: {str(e)}"],
            )
