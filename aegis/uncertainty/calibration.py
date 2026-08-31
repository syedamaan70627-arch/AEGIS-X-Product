"""
AEGIS-X Platt Calibration Module.

Provides probability calibration via Platt scaling without data leakage.
"""

from typing import Any, Dict, Optional, Union
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from aegis.core.exceptions import DatasetValidationError


class PlattCalibrator:
    """
    Platt probability calibrator using Logistic Regression on uncalibrated model probabilities/logits.
    """

    def __init__(self, random_state: int = 42) -> None:
        self.calibrator: LogisticRegression = LogisticRegression(C=1.0, random_state=random_state)
        self.is_fitted: bool = False

    def _probability_to_logit(self, probabilities: np.ndarray, eps: float = 1e-7) -> np.ndarray:
        """Converts probabilities to logit scale with clipping to avoid numerical explosion."""
        p_clipped = np.clip(probabilities, eps, 1.0 - eps)
        return np.log(p_clipped / (1.0 - p_clipped))

    def fit(
        self,
        uncalibrated_probs: Union[np.ndarray, list],
        y_true: Union[np.ndarray, pd.Series, list],
    ) -> "PlattCalibrator":
        """Fits Platt calibrator on a dedicated calibration dataset split."""
        p_arr = np.array(uncalibrated_probs, copy=True)
        y_arr = np.array(y_true, copy=True)

        if len(p_arr) != len(y_arr):
            raise DatasetValidationError(
                f"Length mismatch: probabilities length ({len(p_arr)}) != ground truth length ({len(y_arr)})."
            )

        if len(p_arr) < 5:
            raise DatasetValidationError("PlattCalibrator requires at least 5 samples to fit.")

        # Ensure probabilities are 2D logits if binary
        if p_arr.ndim == 1 or (p_arr.ndim == 2 and p_arr.shape[1] == 1):
            p_flat = p_arr.ravel()
            logits = self._probability_to_logit(p_flat).reshape(-1, 1)
        else:
            # Multi-class: use maximum probability logit
            max_p = np.max(p_arr, axis=1)
            logits = self._probability_to_logit(max_p).reshape(-1, 1)

        self.calibrator.fit(logits, y_arr)
        self.is_fitted = True
        return self

    def calibrate(self, uncalibrated_probs: np.ndarray) -> np.ndarray:
        """Calibrates uncalibrated model probabilities using fitted Platt model."""
        if not self.is_fitted:
            raise DatasetValidationError("PlattCalibrator must be fitted before calling calibrate().")

        p_arr = np.array(uncalibrated_probs, copy=True)
        if p_arr.ndim == 1 or (p_arr.ndim == 2 and p_arr.shape[1] == 1):
            p_flat = p_arr.ravel()
            logits = self._probability_to_logit(p_flat).reshape(-1, 1)
            calib_p1 = self.calibrator.predict_proba(logits)[:, 1]
            return np.column_stack([1.0 - calib_p1, calib_p1])
        else:
            max_p = np.max(p_arr, axis=1)
            logits = self._probability_to_logit(max_p).reshape(-1, 1)
            calib_max_p = self.calibrator.predict_proba(logits)[:, 1]
            # Rescale class probabilities proportionally
            scaling_factor = calib_max_p / np.maximum(max_p, 1e-12)
            calibrated = p_arr * scaling_factor[:, np.newaxis]
            # Re-normalize rows to sum to 1.0
            row_sums = np.sum(calibrated, axis=1, keepdims=True)
            return calibrated / np.maximum(row_sums, 1e-12)
