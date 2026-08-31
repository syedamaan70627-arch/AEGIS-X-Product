"""
AEGIS-X Evaluation Metrics Calculator Module.

Shared metrics calculation utility for research evaluation routines.
"""

from typing import Dict, Union
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from aegis.core.contracts import AblationMetrics


class EvaluationMetricsCalculator:
    """
    Computes state-level evaluation metrics (AUROC, AUPR, Precision, Recall, F1).
    """

    @staticmethod
    def calculate_metrics(
        y_true: Union[np.ndarray, pd.Series],
        probabilities: Union[np.ndarray, pd.Series],
        threshold: float = 0.5,
    ) -> AblationMetrics:
        """
        Computes standard classification evaluation metrics given ground truth and prediction probabilities.
        """
        y_arr = np.asarray(y_true, dtype=int)
        probs = np.asarray(probabilities, dtype=np.float64)
        preds = (probs >= threshold).astype(int)

        n_classes = len(np.unique(y_arr))
        auc = float(roc_auc_score(y_arr, probs)) if n_classes > 1 else 0.5
        aupr = float(average_precision_score(y_arr, probs)) if n_classes > 1 else 0.5

        rec = float(recall_score(y_arr, preds, zero_division=0))
        prec = float(precision_score(y_arr, preds, zero_division=0))
        f1 = float(f1_score(y_arr, preds, zero_division=0))

        return AblationMetrics(
            auroc=auc,
            aupr=aupr,
            precision=prec,
            recall=rec,
            f1=f1,
            threshold=float(threshold),
        )
