"""
Unit tests for AEGIS-X Uncertainty Estimator and PlattCalibrator modules.
"""

from unittest.mock import MagicMock
import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import RidgeClassifier

from aegis.core.contracts import ReliabilityStatus, TaskType
from aegis.core.model_adapter import SklearnModelAdapter
from aegis.uncertainty.calibration import PlattCalibrator
from aegis.uncertainty.estimator import UncertaintyEstimator


@pytest.fixture
def trained_rf_model():
    np.random.seed(42)
    X = np.random.normal(size=(100, 4))
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    rf = RandomForestClassifier(n_estimators=20, random_state=42)
    rf.fit(X, y)

    adapter = SklearnModelAdapter(rf)
    return adapter, X, y


def test_uncertainty_predictive_entropy(trained_rf_model):
    adapter, X, _ = trained_rf_model

    estimator = UncertaintyEstimator(method="predictive_entropy")
    res = estimator.analyze(X[:10], model_adapter=adapter)

    assert res.status == ReliabilityStatus.AVAILABLE
    assert res.method == "predictive_entropy"
    assert res.probabilities.shape == (10, 2)
    assert len(res.uncertainty_scores) == 10
    assert not res.is_calibrated  # Raw probabilities used
    assert any("raw uncalibrated" in w for w in res.warnings)


def test_uncertainty_platt_calibration(trained_rf_model):
    adapter, X, y = trained_rf_model

    # Use first 50 as calibration set, last 50 as eval set
    raw_calib_probs = adapter.predict_proba(X[:50])

    estimator = UncertaintyEstimator(method="predictive_entropy")
    estimator.fit_calibrator(raw_calib_probs, y[:50])

    res = estimator.analyze(X[50:], model_adapter=adapter)

    assert res.status == ReliabilityStatus.AVAILABLE
    assert res.is_calibrated
    assert res.probabilities.shape == (50, 2)
    # Calibrated probabilities rows must sum to 1.0
    np.testing.assert_allclose(np.sum(res.probabilities, axis=1), np.ones(50), atol=1e-5)


def test_uncertainty_unsupported_predict_proba():
    # RidgeClassifier does not support predict_proba
    ridge = RidgeClassifier()
    X = np.random.normal(size=(20, 3))
    y = np.random.randint(0, 2, size=20)
    ridge.fit(X, y)

    adapter = SklearnModelAdapter(ridge)

    estimator = UncertaintyEstimator()
    res = estimator.analyze(X, model_adapter=adapter)

    assert res.status == ReliabilityStatus.NOT_AVAILABLE
    assert "does not support predict_proba" in res.warnings[0]


def test_uncertainty_numerical_stability():
    estimator = UncertaintyEstimator()
    # Edge case probabilities: exactly 0.0 and 1.0, and balanced 0.5
    edge_probs = np.array([[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]])

    entropy_scores = estimator._compute_entropy(edge_probs)

    # Entropy of [1.0, 0.0] should be 0.0
    assert np.isclose(entropy_scores[0], 0.0, atol=1e-5)
    assert np.isclose(entropy_scores[1], 0.0, atol=1e-5)
    # Entropy of [0.5, 0.5] should be 1.0 bit
    assert np.isclose(entropy_scores[2], 1.0, atol=1e-5)


def test_uncertainty_no_true_label_dependency(trained_rf_model):
    adapter, X, _ = trained_rf_model

    estimator = UncertaintyEstimator()
    # analyze method requires only evaluation data and model adapter
    res = estimator.analyze(X[:5], model_adapter=adapter)

    assert res.status == ReliabilityStatus.AVAILABLE
    assert len(res.uncertainty_scores) == 5
