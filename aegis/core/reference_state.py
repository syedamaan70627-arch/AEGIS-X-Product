"""
AEGIS-X Reference State Module.

Encapsulates nominal system reference statistics, covariance structures,
normalized reference matrices, and empirical distribution baselines.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from aegis.core.exceptions import DatasetValidationError
from aegis.core.preprocessing import FeaturePreprocessor


class ReferenceState:
    """
    Fitted reference baseline state representing nominal system operating conditions.
    """

    def __init__(
        self,
        feature_names: Optional[List[str]] = None,
        regularization_eps: float = 1e-6,
    ) -> None:
        self.feature_names: Optional[List[str]] = feature_names
        self.regularization_eps: float = regularization_eps
        self.preprocessor: FeaturePreprocessor = FeaturePreprocessor(feature_names=feature_names)
        
        self.is_fitted: bool = False
        self.num_samples: int = 0
        self.num_features: int = 0
        
        self.X_ref_raw: Optional[np.ndarray] = None
        self.X_ref_scaled: Optional[np.ndarray] = None
        self.y_ref: Optional[np.ndarray] = None
        
        self.mean_vector: Optional[np.ndarray] = None
        self.cov_matrix: Optional[np.ndarray] = None
        self.inv_cov_matrix: Optional[np.ndarray] = None
        
        self.empirical_distributions: Dict[str, np.ndarray] = {}

    def fit(
        self,
        X_ref: Union[pd.DataFrame, np.ndarray],
        y_ref: Optional[Union[pd.Series, np.ndarray]] = None,
    ) -> "ReferenceState":
        """Fits reference state statistics on nominal training/reference data."""
        self.X_ref_scaled = self.preprocessor.fit_transform(X_ref)
        self.feature_names = self.preprocessor.feature_names
        self.num_samples, self.num_features = self.X_ref_scaled.shape

        if self.num_samples < 2:
            raise DatasetValidationError(
                f"ReferenceState requires at least 2 samples to compute covariance, got {self.num_samples}."
            )

        if y_ref is not None:
            if isinstance(y_ref, (pd.Series, pd.DataFrame)):
                self.y_ref = y_ref.to_numpy(copy=True)
            else:
                self.y_ref = np.array(y_ref, copy=True)

        # Compute mean vector and covariance matrix
        self.mean_vector = np.mean(self.X_ref_scaled, axis=0)
        self.cov_matrix = np.cov(self.X_ref_scaled, rowvar=False)

        # Handle 1D feature edge case
        if self.num_features == 1:
            self.cov_matrix = np.array([[self.cov_matrix]])
            self.mean_vector = np.array([self.mean_vector])

        # Regularized inverse covariance
        reg_cov = self.cov_matrix + self.regularization_eps * np.eye(self.num_features)
        self.inv_cov_matrix = np.linalg.pinv(reg_cov)

        self.is_fitted = True
        return self

    def register_empirical_distribution(self, name: str, scores: np.ndarray) -> None:
        """Registers empirical reference scores (e.g. Mahalanobis distance) for percentile transformation."""
        self.empirical_distributions[name] = np.sort(np.array(scores, copy=True))

    def get_empirical_percentile(self, name: str, value: float) -> float:
        """Computes empirical percentile risk score in [0, 1] relative to reference distribution."""
        if name not in self.empirical_distributions:
            return 0.5
        ref_scores = self.empirical_distributions[name]
        if len(ref_scores) == 0:
            return 0.5
        pos = np.searchsorted(ref_scores, value, side="right")
        return float(pos / len(ref_scores))

    def get_empirical_percentiles(self, name: str, values: np.ndarray) -> np.ndarray:
        """Computes empirical percentile risk array for evaluation scores."""
        if name not in self.empirical_distributions:
            return np.full_like(values, 0.5, dtype=np.float64)
        ref_scores = self.empirical_distributions[name]
        if len(ref_scores) == 0:
            return np.full_like(values, 0.5, dtype=np.float64)
        positions = np.searchsorted(ref_scores, values, side="right")
        return positions.astype(np.float64) / float(len(ref_scores))
