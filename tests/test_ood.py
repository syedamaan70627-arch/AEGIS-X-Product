"""
Unit tests for AEGIS-X Out-of-Distribution (OOD) Detector module.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.core.contracts import ReliabilityStatus
from aegis.core.exceptions import DatasetValidationError
from aegis.ood.detector import OODDetector


@pytest.fixture
def nominal_data():
    np.random.seed(42)
    return np.random.multivariate_normal(
        mean=[0.0, 0.0, 0.0],
        cov=[[1.0, 0.2, 0.1], [0.2, 1.0, 0.2], [0.1, 0.2, 1.0]],
        size=200,
    )


@pytest.fixture
def ood_shifted_data():
    np.random.seed(123)
    return np.random.multivariate_normal(
        mean=[5.0, 5.0, 5.0],
        cov=[[2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]],
        size=50,
    )


def test_ood_mahalanobis_fit_and_analyze(nominal_data, ood_shifted_data):
    detector = OODDetector(method="mahalanobis")
    detector.fit(nominal_data)

    assert detector.is_fitted
    assert detector.threshold is not None

    in_dist_res = detector.analyze(nominal_data[:20])
    out_dist_res = detector.analyze(ood_shifted_data)

    assert in_dist_res.status == ReliabilityStatus.AVAILABLE
    assert out_dist_res.status == ReliabilityStatus.AVAILABLE

    # Out-of-distribution risk should be significantly higher than in-distribution risk
    assert out_dist_res.aggregate_risk > in_dist_res.aggregate_risk
    assert out_dist_res.aggregate_risk > 0.8


def test_ood_isolation_forest(nominal_data, ood_shifted_data):
    detector = OODDetector(method="isolation_forest", random_state=42)
    detector.fit(nominal_data)

    in_dist_res = detector.analyze(nominal_data[:20])
    out_dist_res = detector.analyze(ood_shifted_data)

    assert in_dist_res.status == ReliabilityStatus.AVAILABLE
    assert out_dist_res.aggregate_risk > in_dist_res.aggregate_risk


def test_ood_ensemble(nominal_data, ood_shifted_data):
    detector = OODDetector(method="ensemble", random_state=42)
    detector.fit(nominal_data)

    res = detector.analyze(ood_shifted_data)
    assert res.status == ReliabilityStatus.AVAILABLE
    assert res.method == "ensemble"
    assert len(res.risk_scores) == 50


def test_ood_deterministic_behavior(nominal_data, ood_shifted_data):
    det1 = OODDetector(method="isolation_forest", random_state=42)
    det1.fit(nominal_data)
    res1 = det1.analyze(ood_shifted_data)

    det2 = OODDetector(method="isolation_forest", random_state=42)
    det2.fit(nominal_data)
    res2 = det2.analyze(ood_shifted_data)

    np.testing.assert_allclose(res1.scores, res2.scores)
    np.testing.assert_allclose(res1.risk_scores, res2.risk_scores)


def test_ood_input_copy_safety(nominal_data):
    df_eval = pd.DataFrame(nominal_data[:10], columns=["f1", "f2", "f3"])
    df_eval_copy = df_eval.copy(deep=True)

    detector = OODDetector(method="mahalanobis")
    detector.fit(nominal_data)
    _ = detector.analyze(df_eval)

    # Input DataFrame should not be mutated
    pd.testing.assert_frame_equal(df_eval, df_eval_copy)


def test_ood_no_label_dependency(nominal_data):
    detector = OODDetector(method="mahalanobis")
    detector.fit(nominal_data)

    # analyze method accepts only feature matrix, no label argument
    res = detector.analyze(nominal_data[:5])
    assert res.status == ReliabilityStatus.AVAILABLE
    assert len(res.scores) == 5


def test_ood_unfitted_call():
    detector = OODDetector(method="mahalanobis")
    res = detector.analyze(np.array([[1.0, 2.0, 3.0]]))

    assert res.status == ReliabilityStatus.NOT_AVAILABLE
    assert "must be fitted" in res.warnings[0]
