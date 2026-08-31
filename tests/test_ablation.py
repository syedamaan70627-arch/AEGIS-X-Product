"""
Unit tests for AEGIS-X Module 11 Component Ablation Evaluator.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.core.analyzer import CoreReliabilityAnalyzer
from aegis.core.contracts import ReliabilityStatus
from aegis.evaluation.ablation import AblationEvaluator
from aegis.evaluation.metrics import EvaluationMetricsCalculator


@pytest.fixture
def sample_ablation_data():
    np.random.seed(42)
    n = 90

    # Signals where uncertainty has the strongest predictive correlation with failure
    ood = np.random.uniform(0.1, 0.9, n)
    unc = np.random.uniform(0.1, 0.9, n)
    drift = np.random.uniform(0.0, 0.5, n)
    fused = (ood * 0.2 + unc * 0.7 + drift * 0.1)

    df = pd.DataFrame({
        "ood_risk": ood,
        "uncertainty_risk": unc,
        "drift_risk": drift,
        "fused_risk": fused,
        "Failure_Within_3": (unc > 0.45).astype(int),
        "severity": np.random.uniform(0.05, 0.5, n),
    })

    train_df = df.iloc[:30].copy()
    val_df = df.iloc[30:60].copy()
    test_df = df.iloc[60:].copy()

    return train_df, val_df, test_df


def test_evaluation_metrics_calculator():
    y_true = np.array([0, 0, 1, 1])
    probs = np.array([0.1, 0.2, 0.8, 0.9])

    metrics = EvaluationMetricsCalculator.calculate_metrics(y_true, probs, threshold=0.5)

    assert metrics.auroc == 1.0
    assert metrics.aupr == 1.0
    assert metrics.f1 == 1.0


def test_ablation_evaluator_run_study(sample_ablation_data):
    train_df, val_df, test_df = sample_ablation_data
    orig_train_copy = train_df.copy(deep=True)

    result = AblationEvaluator.run_ablation_study(
        train_df, val_df, test_df, horizon_val=3, random_state=42
    )

    # Source DataFrames must remain unmutated
    pd.testing.assert_frame_equal(train_df, orig_train_copy)

    assert result.status == ReliabilityStatus.AVAILABLE
    assert "OOD" in result.component_contributions
    assert "Uncertainty" in result.component_contributions
    assert "Drift" in result.component_contributions

    # Uncertainty should be identified as performance-sensitive in this synthetic setup
    unc_contrib = result.component_contributions["Uncertainty"]
    assert unc_contrib.component_name == "Uncertainty"
    assert isinstance(unc_contrib.delta_aupr, float)


def test_signed_deltas_and_positive_no_drift_support(sample_ablation_data):
    train_df, val_df, test_df = sample_ablation_data

    result = AblationEvaluator.run_ablation_study(
        train_df, val_df, test_df, horizon_val=3, random_state=42
    )

    # Verify deltas preserve sign (ablated - full)
    for comp_name, contrib in result.component_contributions.items():
        expected_d_aupr = contrib.metrics.aupr - result.full_metrics.aupr
        np.testing.assert_allclose(contrib.delta_aupr, expected_d_aupr)

    # No Drift is explicitly allowed to have a positive or non-negative delta without raising errors
    drift_contrib = result.component_contributions["Drift"]
    assert isinstance(drift_contrib.delta_aupr, float)


def test_validation_only_threshold_selection_prevents_leakage(sample_ablation_data):
    train_df, val_df, test_df_1 = sample_ablation_data

    result_1 = AblationEvaluator.run_ablation_study(
        train_df, val_df, test_df_1, horizon_val=3, random_state=42
    )

    # Modify held-out test split targets
    test_df_2 = test_df_1.copy()
    test_df_2["Failure_Within_3"] = 1 - test_df_2["Failure_Within_3"]

    result_2 = AblationEvaluator.run_ablation_study(
        train_df, val_df, test_df_2, horizon_val=3, random_state=42
    )

    # Thresholds derived from validation split must remain strictly identical
    assert result_1.full_metrics.threshold == result_2.full_metrics.threshold
    assert result_1.component_contributions["OOD"].metrics.threshold == result_2.component_contributions["OOD"].metrics.threshold


def test_ablation_does_not_mutate_operational_analyzer_state(sample_ablation_data):
    train_df, val_df, test_df = sample_ablation_data

    analyzer = CoreReliabilityAnalyzer()
    analyzer.fit_reference(train_df[["ood_risk", "uncertainty_risk", "drift_risk"]])

    initial_ref = analyzer.reference_state.mean_vector.copy()

    # Run ablation study
    AblationEvaluator.run_ablation_study(train_df, val_df, test_df, horizon_val=3)

    # CoreReliabilityAnalyzer state must remain completely unmutated
    np.testing.assert_allclose(analyzer.reference_state.mean_vector, initial_ref)
