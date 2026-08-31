"""
Unit tests for AEGIS-X CoreReliabilityAnalyzer module.
"""

import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier

from aegis.core.analyzer import CoreReliabilityAnalyzer
from aegis.core.contracts import CoreReliabilityResult, ReliabilityStatus, TaskType
from aegis.core.model_adapter import SklearnModelAdapter


@pytest.fixture
def core_test_setup():
    np.random.seed(42)
    X_ref = np.random.normal(loc=0.0, scale=1.0, size=(150, 4))
    y_ref = (X_ref[:, 0] + X_ref[:, 1] > 0).astype(int)

    rf = RandomForestClassifier(n_estimators=10, random_state=42)
    rf.fit(X_ref, y_ref)

    adapter = SklearnModelAdapter(rf)

    X_eval_clean = np.random.normal(loc=0.0, scale=1.0, size=(30, 4))
    X_eval_shifted = np.random.normal(loc=4.0, scale=1.5, size=(30, 4))

    return adapter, X_ref, y_ref, X_eval_clean, X_eval_shifted


def test_core_reliability_analyzer_flow(core_test_setup):
    adapter, X_ref, y_ref, X_eval_clean, X_eval_shifted = core_test_setup

    analyzer = CoreReliabilityAnalyzer()
    analyzer.fit_reference(
        reference_data=X_ref,
        feature_names=["f1", "f2", "f3", "f4"],
        calibration_data=X_ref[:50],
        calibration_labels=y_ref[:50],
        model_adapter=adapter,
    )

    assert analyzer.is_fitted

    res_clean: CoreReliabilityResult = analyzer.analyze(X_eval_clean, model_adapter=adapter)
    res_shifted: CoreReliabilityResult = analyzer.analyze(X_eval_shifted, model_adapter=adapter)

    # Validate Result Structure
    assert res_clean.ood.status == ReliabilityStatus.AVAILABLE
    assert res_clean.uncertainty.status == ReliabilityStatus.AVAILABLE
    assert res_clean.drift.status == ReliabilityStatus.AVAILABLE

    assert res_clean.uncertainty.is_calibrated

    # Shifted evaluation should yield higher OOD risk and higher drift score
    assert res_shifted.ood.aggregate_risk > res_clean.ood.aggregate_risk
    assert res_shifted.drift.aggregate_drift_score > res_clean.drift.aggregate_drift_score

    # Check Capability Summary
    summary = res_shifted.capability_summary
    assert "aggregate_ood_risk" in summary
    assert "aggregate_uncertainty" in summary
    assert "aggregate_drift_score" in summary
    assert "drift_detected" in summary
