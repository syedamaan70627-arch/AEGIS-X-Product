"""
Unit tests for AEGIS-X Failure Discovery Engine.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.core.contracts import ReliabilityStatus
from aegis.faults.failure_discovery import FailureDiscoveryEngine
from aegis.faults.transformations import inject_feature_bias


@pytest.fixture
def sample_data():
    np.random.seed(42)
    df = pd.DataFrame(
        np.random.normal(loc=1.0, scale=0.5, size=(30, 3)),
        columns=["f1", "f2", "f3"],
    )
    y_true = np.random.choice([0, 1], size=30)
    return df, y_true


class DummyModelAdapter:
    def __init__(self):
        self.supports_predict_proba = True

    def predict(self, X):
        # Predict 1 if first feature > 1.2 else 0
        arr = X.to_numpy() if isinstance(X, pd.DataFrame) else X
        return (arr[:, 0] > 1.2).astype(int)

    def predict_proba(self, X):
        preds = self.predict(X)
        probs = np.zeros((len(X), 2))
        probs[:, 1] = np.where(preds == 1, 0.9, 0.1)
        probs[:, 0] = 1.0 - probs[:, 1]
        return probs


def test_failure_discovery_label_free_mode(sample_data):
    df, _ = sample_data
    faulted = inject_feature_bias(df, severity=0.5, seed=42)
    model = DummyModelAdapter()

    engine = FailureDiscoveryEngine(default_risk_threshold=0.5)
    res = engine.discover_failures(
        faulted_data=faulted,
        original_data=df,
        y_true=None,  # Label-free mode
        model_adapter=model,
    )

    assert res.status == ReliabilityStatus.AVAILABLE
    assert not res.is_label_aware
    assert res.total_failures is None
    assert res.silent_failures is None
    assert res.silent_failure_rate is None
    assert len(res.failure_events) == 30

    # Label-free event has_actual_failure & is_silent_failure must be None
    assert res.failure_events[0].has_actual_failure is None
    assert res.failure_events[0].is_silent_failure is None


def test_failure_discovery_label_aware_mode(sample_data):
    df, y_true = sample_data
    faulted = inject_feature_bias(df, severity=0.5, seed=42)
    model = DummyModelAdapter()

    engine = FailureDiscoveryEngine(default_risk_threshold=0.5)
    res = engine.discover_failures(
        faulted_data=faulted,
        original_data=df,
        y_true=y_true,  # Label-aware mode
        model_adapter=model,
    )

    assert res.status == ReliabilityStatus.AVAILABLE
    assert res.is_label_aware
    assert res.total_failures is not None
    assert res.silent_failures is not None
    assert 0.0 <= (res.silent_failure_rate or 0.0) <= 1.0
    assert len(res.failure_events) == 30

    # Confirmed silent failure rule: actual_failure == True AND high_risk_warning == False
    for ev in res.failure_events:
        if ev.has_actual_failure and not ev.is_high_risk_warning:
            assert ev.is_silent_failure is True
        elif ev.has_actual_failure:
            assert ev.is_silent_failure is False
