"""
Unit tests for Trajectory-Level Early Warning Evaluation and False Warning Diagnostics.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.warning.engine import EarlyWarningEngine
from aegis.warning.horizon import EarlyWarningHorizonEvaluator


def test_false_trajectory_warning_identification():
    # Trajectory 0: Fails at index 3. Warning triggered at index 1.
    # Trajectory 1: Non-failing. Warning triggered at index 1 -> False trajectory warning!
    df = pd.DataFrame({
        "trajectory_id": [0, 0, 0, 0, 1, 1, 1, 1],
        "Failure_Rate": [0.0, 0.0, 0.0, 0.2, 0.0, 0.0, 0.0, 0.0],
        "warning_probability": [0.1, 0.6, 0.8, 0.9, 0.1, 0.7, 0.2, 0.1],
    })

    metrics, results = EarlyWarningHorizonEvaluator.evaluate_trajectories(
        df, horizon_val=3, threshold=0.5, failure_boundary=0.10
    )

    assert metrics["failing_trajectories"] == 1
    assert metrics["warned_failing_trajectories"] == 1
    assert metrics["early_warning_coverage"] == 1.0

    assert metrics["non_failing_trajectories"] == 1
    assert metrics["false_trajectory_warnings"] == 1
    # False trajectory warning rate must equal 1.0 (100%)
    assert metrics["false_trajectory_warning_rate"] == 1.0
    assert results[1].is_false_trajectory_warning is True


def test_heldout_labels_cannot_alter_warning_threshold():
    np.random.seed(42)
    n = 60
    df = pd.DataFrame({
        "ood_risk": np.random.uniform(0.1, 0.9, n),
        "uncertainty_risk": np.random.uniform(0.1, 0.9, n),
        "drift_risk": np.random.uniform(0.0, 0.5, n),
        "fused_risk": np.random.uniform(0.1, 0.9, n),
        "Failure_Within_3": np.array([1 if (i % 3 == 0) else 0 for i in range(n)]),
    })

    train_df = df.iloc[:25].copy()
    val_df = df.iloc[25:45].copy()
    test_df_1 = df.iloc[45:].copy()

    engine = EarlyWarningEngine(horizon_val=3, random_state=42)
    engine.fit(train_df, val_df)
    initial_threshold = engine.warning_threshold

    res1 = engine.predict_warning(test_df_1)

    # Invert test set targets
    test_df_2 = test_df_1.copy()
    test_df_2["Failure_Within_3"] = 1 - test_df_2["Failure_Within_3"]

    res2 = engine.predict_warning(test_df_2)

    # Threshold must remain strictly identical
    assert engine.warning_threshold == initial_threshold
    assert res1.threshold == res2.threshold
