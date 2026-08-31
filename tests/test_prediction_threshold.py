"""
Unit tests for Validation-Only Threshold Selection and Leakage Prevention.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.prediction.engine import FailurePredictor
from aegis.prediction.threshold import ValidationThresholdSelector


def test_validation_threshold_selection():
    np.random.seed(42)
    y_val = np.array([0, 0, 1, 1, 0, 1, 0, 0, 1, 0])
    probs = np.array([0.1, 0.2, 0.8, 0.7, 0.3, 0.9, 0.2, 0.4, 0.65, 0.15])

    thresh_info = ValidationThresholdSelector.select_best_threshold(y_val, probs)

    assert thresh_info.selection_split == "validation"
    assert 0.05 <= thresh_info.threshold <= 0.95
    assert thresh_info.validation_f1 > 0.0


def test_heldout_labels_cannot_alter_threshold():
    """
    CRITICAL SAFETY TEST:
    Proves that altering held-out test set labels or data CANNOT modify
    the previously selected validation threshold.
    """
    np.random.seed(42)
    n = 50
    df = pd.DataFrame({
        "ood_risk": np.random.uniform(0.1, 0.9, n),
        "uncertainty_risk": np.random.uniform(0.1, 0.9, n),
        "drift_risk": np.random.uniform(0.0, 0.5, n),
        "fused_risk": np.random.uniform(0.1, 0.9, n),
        "Failure_Onset_Next": np.random.choice([0, 1], size=n),
    })

    train_df = df.iloc[:20].copy()
    val_df = df.iloc[20:35].copy()
    test_df_1 = df.iloc[35:].copy()

    # Fit predictor on train & validation
    predictor = FailurePredictor(random_state=42)
    predictor.fit(train_df, val_df)
    initial_threshold = predictor.threshold_info.threshold

    # Predict on initial test split
    res1 = predictor.predict(test_df_1, y_true_onset=test_df_1["Failure_Onset_Next"])

    # Create modified test split with inverted ground-truth labels
    test_df_2 = test_df_1.copy()
    test_df_2["Failure_Onset_Next"] = 1 - test_df_2["Failure_Onset_Next"]

    # Predict on modified test split
    res2 = predictor.predict(test_df_2, y_true_onset=test_df_2["Failure_Onset_Next"])

    # ASSERTION: The threshold MUST remain exactly identical!
    assert predictor.threshold_info.threshold == initial_threshold
    assert res1.predictions[0].threshold == res2.predictions[0].threshold
