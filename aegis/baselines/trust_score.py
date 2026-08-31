"""
AEGIS-X Trust Score Baseline (Jiang et al., NeurIPS 2018).

Implements the model-agnostic Trust Score algorithm as an empirical baseline for
class-conditional distance reliability evaluation.
"""

from typing import Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.neighbors import NearestNeighbors


class TrustScoreBaseline:
    """
    Implements Trust Score (Jiang et al., NeurIPS 2018):
    Ratio of distance to nearest sample in non-predicted class vs distance to nearest sample in predicted class.
    """

    def __init__(self, k: int = 5, alpha: float = 0.0) -> None:
        self.k: int = k
        self.alpha: float = alpha
        self.class_neighbors: dict = {}
        self.classes: np.ndarray = np.array([])
        self.is_fitted: bool = False

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Union[pd.Series, np.ndarray]) -> "TrustScoreBaseline":
        """Fits nearest neighbor estimators per class."""
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y, dtype=int)
        self.classes = np.unique(y_arr)

        for c in self.classes:
            X_c = X_arr[y_arr == c]
            if len(X_c) > 0:
                nn = NearestNeighbors(n_neighbors=min(self.k, len(X_c)))
                nn.fit(X_c)
                self.class_neighbors[c] = (nn, X_c)

        self.is_fitted = True
        return self

    def compute_trust_scores(
        self, X: Union[pd.DataFrame, np.ndarray], model_adapter: Any
    ) -> np.ndarray:
        """Computes Trust Score ratio for query samples."""
        if not self.is_fitted:
            raise ValueError("TrustScoreBaseline is not fitted.")

        X_arr = np.asarray(X, dtype=float)
        preds = model_adapter.predict(X_arr)
        n_samples = len(X_arr)
        trust_scores = np.zeros(n_samples)

        for i in range(n_samples):
            pred_class = preds[i]
            x_i = X_arr[i : i + 1]

            # Distance to predicted class
            if pred_class in self.class_neighbors:
                nn_pred, _ = self.class_neighbors[pred_class]
                d_pred, _ = nn_pred.kneighbors(x_i, n_neighbors=1)
                d_pred_val = float(d_pred[0][0])
            else:
                d_pred_val = 1e-5

            # Distance to nearest non-predicted class
            d_other_min = float("inf")
            for c in self.classes:
                if c != pred_class and c in self.class_neighbors:
                    nn_c, _ = self.class_neighbors[c]
                    d_c, _ = nn_c.kneighbors(x_i, n_neighbors=1)
                    d_val = float(d_c[0][0])
                    if d_val < d_other_min:
                        d_other_min = d_val

            if d_other_min == float("inf"):
                d_other_min = d_pred_val + 1.0

            # Trust Score = d_other / (d_pred + eps)
            trust_scores[i] = d_other_min / (d_pred_val + 1e-6)

        return trust_scores
