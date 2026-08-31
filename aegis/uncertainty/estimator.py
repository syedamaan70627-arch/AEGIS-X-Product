"""
AEGIS-X Uncertainty Estimator Module.

Migrates Module 3 research logic: predictive entropy, confidence-based uncertainty,
and Platt calibration integration without data leakage.
"""

from typing import Any, Dict, Optional, Union
import numpy as np
import pandas as pd

from aegis.core.contracts import ReliabilityStatus, UncertaintyResult
from aegis.core.exceptions import DatasetValidationError
from aegis.uncertainty.calibration import PlattCalibrator


class UncertaintyEstimator:
    """
    Uncertainty estimator quantifying epistemic and aleatoric prediction uncertainty
    via predictive entropy and Platt probability calibration.
    """

    def __init__(
        self,
        method: str = "predictive_entropy",
        eps: float = 1e-12,
    ) -> None:
        if method not in ("predictive_entropy", "confidence_uncertainty"):
            raise DatasetValidationError(
                f"Unsupported uncertainty method '{method}'. Supported methods: 'predictive_entropy', 'confidence_uncertainty'."
            )
        self.method: str = method
        self.eps: float = eps
        self.calibrator: Optional[PlattCalibrator] = None

    def fit_calibrator(
        self,
        uncalibrated_probs: np.ndarray,
        y_calibration: Union[np.ndarray, pd.Series, list],
    ) -> "UncertaintyEstimator":
        """Fits Platt calibrator using dedicated calibration split probabilities and true labels."""
        self.calibrator = PlattCalibrator()
        self.calibrator.fit(uncalibrated_probs, y_calibration)
        return self

    def _compute_entropy(self, probabilities: np.ndarray) -> np.ndarray:
        """Computes per-sample predictive entropy H(p) = -sum p_c log2(p_c + eps)."""
        p_clipped = np.maximum(probabilities, self.eps)
        # Normalize rows to guarantee sum to 1
        p_normalized = p_clipped / np.sum(p_clipped, axis=1, keepdims=True)
        entropy = -np.sum(p_normalized * np.log2(p_normalized), axis=1)
        return np.maximum(entropy, 0.0)

    def estimate(self, probabilities: np.ndarray) -> UncertaintyResult:
        """Computes uncertainty result directly from a probability matrix."""
        probs = np.asarray(probabilities, dtype=np.float64)
        if probs.ndim == 1:
            probs = np.column_stack([1.0 - probs, probs])

        if self.method == "predictive_entropy":
            scores = self._compute_entropy(probs)
        else:
            scores = self._compute_confidence_uncertainty(probs)

        return UncertaintyResult(
            status=ReliabilityStatus.AVAILABLE,
            method=self.method,
            probabilities=probs,
            uncertainty_scores=scores,
            aggregate_uncertainty=float(np.mean(scores)),
            is_calibrated=False,
            warnings=[],
            limitations=[
                "Predictive entropy measures probability distribution dispersion.",
            ],
        )

    def analyze(
        self,
        evaluation_data: Union[pd.DataFrame, np.ndarray],
        model_adapter: Any,
    ) -> UncertaintyResult:
        """Computes uncertainty metrics for evaluation samples using model probabilities."""
        if model_adapter is None:
            return UncertaintyResult(
                status=ReliabilityStatus.ERROR,
                method=self.method,
                warnings=["No model_adapter provided for uncertainty analysis."],
                limitations=["Cannot compute uncertainty without a valid model adapter."],
            )

        # Check probability support
        has_prob_support = getattr(
            model_adapter, "supports_predict_proba", getattr(model_adapter, "probability_supported", False)
        )
        if not has_prob_support:
            return UncertaintyResult(
                status=ReliabilityStatus.NOT_AVAILABLE,
                method=self.method,
                warnings=["Model does not support predict_proba(). Raw decision scores unavailable."],
                limitations=["Probability-based uncertainty estimation requires predict_proba capability."],
            )

        try:
            raw_probs = model_adapter.predict_proba(evaluation_data)

            # Ensure 2D probability matrix
            if raw_probs.ndim == 1:
                raw_probs = np.column_stack([1.0 - raw_probs, raw_probs])

            is_calibrated = False
            warnings_list = []

            if self.calibrator is not None and self.calibrator.is_fitted:
                probs = self.calibrator.calibrate(raw_probs)
                is_calibrated = True
            else:
                probs = raw_probs
                warnings_list.append("Using raw uncalibrated probabilities; no fitted PlattCalibrator provided.")

            if self.method == "predictive_entropy":
                scores = self._compute_entropy(probs)
            else:
                scores = self._compute_confidence_uncertainty(probs)

            aggregate_uncertainty = float(np.mean(scores))

            return UncertaintyResult(
                status=ReliabilityStatus.AVAILABLE,
                method=self.method,
                probabilities=probs,
                uncertainty_scores=scores,
                aggregate_uncertainty=aggregate_uncertainty,
                is_calibrated=is_calibrated,
                calibration_info={
                    "is_calibrated": is_calibrated,
                    "num_classes": probs.shape[1],
                    "num_samples": len(scores),
                },
                warnings=warnings_list,
                limitations=[
                    "Predictive entropy measures probability distribution dispersion.",
                    "Uncertainty relies on model probability calibration quality.",
                ],
            )
        except Exception as e:
            return UncertaintyResult(
                status=ReliabilityStatus.ERROR,
                method=self.method,
                warnings=[f"Uncertainty analysis failed: {str(e)}"],
                limitations=["Execution error occurred during uncertainty computation."],
            )
