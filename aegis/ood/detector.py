"""
AEGIS-X Out-of-Distribution (OOD) Detector Module.

Migrates Module 2 research logic: Mahalanobis distance, Isolation Forest,
empirical percentile risk transformation, and label-free OOD scoring.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from aegis.core.contracts import OODResult, ReliabilityStatus
from aegis.core.exceptions import DatasetValidationError
from aegis.core.reference_state import ReferenceState


class OODDetector:
    """
    Out-of-Distribution detector implementing validated Mahalanobis Distance
    and Isolation Forest algorithms.
    """

    def __init__(
        self,
        method: str = "mahalanobis",
        contamination: float = 0.01,
        random_state: int = 42,
    ) -> None:
        if method not in ("mahalanobis", "isolation_forest", "ensemble"):
            raise DatasetValidationError(
                f"Unsupported OOD method '{method}'. Supported methods: 'mahalanobis', 'isolation_forest', 'ensemble'."
            )
        self.method: str = method
        self.contamination: float = contamination
        self.random_state: int = random_state
        
        self.reference_state: Optional[ReferenceState] = None
        self.isolation_forest: Optional[IsolationForest] = None
        self.is_fitted: bool = False

        self.threshold: Optional[float] = None
        self.reference_stats: Dict[str, Any] = {}

    def _compute_mahalanobis_scores(self, X_scaled: np.ndarray, ref_state: ReferenceState) -> np.ndarray:
        """Computes Mahalanobis distance for normalized feature matrix."""
        diff = X_scaled - ref_state.mean_vector
        # Matrix quadratic form: sqrt( sum_j (diff @ inv_cov) * diff )
        dist_sq = np.sum((diff @ ref_state.inv_cov_matrix) * diff, axis=1)
        # Numerical safeguard for near-zero negative float precision
        dist_sq = np.maximum(dist_sq, 0.0)
        return np.sqrt(dist_sq)

    def _compute_isolation_scores(self, X_scaled: np.ndarray) -> np.ndarray:
        """Computes Isolation Forest raw anomaly score (-score_samples)."""
        if self.isolation_forest is None:
            raise DatasetValidationError("Isolation Forest model is not fitted.")
        return -self.isolation_forest.score_samples(X_scaled)

    def fit(
        self,
        reference_data: Union[pd.DataFrame, np.ndarray, ReferenceState],
        feature_names: Optional[List[str]] = None,
    ) -> "OODDetector":
        """Fits OOD reference parameters and Isolation Forest model on nominal reference data."""
        if isinstance(reference_data, ReferenceState):
            if not reference_data.is_fitted:
                raise DatasetValidationError("Provided ReferenceState is not fitted.")
            self.reference_state = reference_data
        else:
            self.reference_state = ReferenceState(feature_names=feature_names)
            self.reference_state.fit(reference_data)

        X_ref_scaled = self.reference_state.X_ref_scaled

        # Fit Isolation Forest
        self.isolation_forest = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=self.random_state,
        )
        self.isolation_forest.fit(X_ref_scaled)

        # Register empirical reference score distributions
        ref_maha = self._compute_mahalanobis_scores(X_ref_scaled, self.reference_state)
        ref_iso = self._compute_isolation_scores(X_ref_scaled)

        self.reference_state.register_empirical_distribution("mahalanobis", ref_maha)
        self.reference_state.register_empirical_distribution("isolation_forest", ref_iso)

        if self.method == "mahalanobis":
            ref_scores = ref_maha
        elif self.method == "isolation_forest":
            ref_scores = ref_iso
        else:  # ensemble
            ref_scores = 0.5 * (
                self.reference_state.get_empirical_percentiles("mahalanobis", ref_maha)
                + self.reference_state.get_empirical_percentiles("isolation_forest", ref_iso)
            )

        self.threshold = float(np.percentile(ref_scores, 95))
        self.reference_stats = {
            "mean": float(np.mean(ref_scores)),
            "std": float(np.std(ref_scores)),
            "max": float(np.max(ref_scores)),
            "min": float(np.min(ref_scores)),
            "p95": self.threshold,
        }

        self.is_fitted = True
        return self

    def analyze(self, evaluation_data: Union[pd.DataFrame, np.ndarray]) -> OODResult:
        """Analyzes evaluation feature vectors for OOD deviation without modifying input or using labels."""
        if not self.is_fitted or self.reference_state is None:
            return OODResult(
                status=ReliabilityStatus.NOT_AVAILABLE,
                method=self.method,
                warnings=["OODDetector must be fitted before running analyze()."],
                limitations=["No reference state fitted."],
            )

        try:
            X_eval_scaled = self.reference_state.preprocessor.transform(evaluation_data)

            if self.method == "mahalanobis":
                scores = self._compute_mahalanobis_scores(X_eval_scaled, self.reference_state)
                risk_scores = self.reference_state.get_empirical_percentiles("mahalanobis", scores)
            elif self.method == "isolation_forest":
                scores = self._compute_isolation_scores(X_eval_scaled)
                risk_scores = self.reference_state.get_empirical_percentiles("isolation_forest", scores)
            else:  # ensemble
                maha_scores = self._compute_mahalanobis_scores(X_eval_scaled, self.reference_state)
                iso_scores = self._compute_isolation_scores(X_eval_scaled)
                maha_risk = self.reference_state.get_empirical_percentiles("mahalanobis", maha_scores)
                iso_risk = self.reference_state.get_empirical_percentiles("isolation_forest", iso_scores)
                scores = 0.5 * (maha_scores + iso_scores)
                risk_scores = 0.5 * (maha_risk + iso_risk)

            aggregate_risk = float(np.mean(risk_scores))

            warnings_list = []
            if aggregate_risk > 0.8:
                warnings_list.append("High aggregate OOD risk detected across evaluation samples.")

            return OODResult(
                status=ReliabilityStatus.AVAILABLE,
                method=self.method,
                scores=scores,
                risk_scores=risk_scores,
                aggregate_risk=aggregate_risk,
                threshold=self.threshold,
                reference_stats=self.reference_stats,
                detector_metadata={
                    "num_samples": len(scores),
                    "num_features": self.reference_state.num_features,
                    "contamination": self.contamination,
                    "random_state": self.random_state,
                },
                warnings=warnings_list,
                limitations=[
                    "OOD detection measures feature space distance/isolation from reference.",
                    "OOD scores assume feature standardization against nominal reference data.",
                ],
            )
        except Exception as e:
            return OODResult(
                status=ReliabilityStatus.ERROR,
                method=self.method,
                warnings=[f"OOD analysis failed: {str(e)}"],
                limitations=["Execution error occurred during OOD scoring."],
            )
