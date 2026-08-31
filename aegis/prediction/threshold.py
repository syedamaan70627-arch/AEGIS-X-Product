"""
AEGIS-X Validation Threshold Selector Module.

Selects onset warning thresholds using VALIDATION DATA ONLY (Module 9R).
"""

from typing import Tuple
import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score

from aegis.core.contracts import PredictionThresholdInfo


class ValidationThresholdSelector:
    """
    Selects optimal failure warning thresholds on validation splits to prevent
    threshold tuning on held-out test data.
    """

    @staticmethod
    def select_best_threshold(
        y_val_onset: np.ndarray,
        val_probabilities: np.ndarray,
        metric: str = "f1",
    ) -> PredictionThresholdInfo:
        """
        Evaluates candidate thresholds strictly on validation data to maximize F1 score.
        """
        y_true = np.asarray(y_val_onset, dtype=int)
        probs = np.asarray(val_probabilities, dtype=np.float64)

        if np.sum(y_true) == 0:
            # Fallback if validation split has 0 positive onset events
            return PredictionThresholdInfo(
                threshold=0.5,
                selection_metric=metric,
                selection_split="validation",
                validation_f1=0.0,
                validation_recall=0.0,
                validation_precision=0.0,
            )

        candidate_thresholds = np.linspace(0.05, 0.95, 91)
        best_thresh = 0.5
        best_f1 = -1.0
        best_rec = 0.0
        best_prec = 0.0

        for t in candidate_thresholds:
            preds = (probs >= t).astype(int)
            rec = float(recall_score(y_true, preds, zero_division=0))
            prec = float(precision_score(y_true, preds, zero_division=0))
            f1 = float(f1_score(y_true, preds, zero_division=0))

            if f1 > best_f1:
                best_f1 = f1
                best_thresh = float(t)
                best_rec = rec
                best_prec = prec

        return PredictionThresholdInfo(
            threshold=best_thresh,
            selection_metric=metric,
            selection_split="validation",
            validation_f1=best_f1,
            validation_recall=best_rec,
            validation_precision=best_prec,
        )
