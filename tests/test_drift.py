"""
Unit tests for AEGIS-X Drift Detector and ADWINWrapper modules.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.core.contracts import ReliabilityStatus
from aegis.drift.adwin_wrapper import ADWINWrapper
from aegis.drift.detector import DriftDetector


@pytest.fixture
def reference_data():
    np.random.seed(42)
    return np.random.normal(loc=0.0, scale=1.0, size=(200, 4))


@pytest.fixture
def in_distribution_eval():
    np.random.seed(43)
    return np.random.normal(loc=0.0, scale=1.0, size=(100, 4))


@pytest.fixture
def shifted_eval_data():
    np.random.seed(99)
    # Significant mean shift on 3 out of 4 features
    return np.random.normal(loc=3.5, scale=1.5, size=(100, 4))


def test_drift_identical_reference_data(reference_data, in_distribution_eval):
    detector = DriftDetector(method="ks_test", alpha=0.05)
    detector.fit(reference_data)

    res = detector.analyze(in_distribution_eval)

    assert res.status == ReliabilityStatus.AVAILABLE
    assert not res.drift_detected
    assert res.aggregate_drift_score < 0.2


def test_drift_shifted_data(reference_data, shifted_eval_data):
    detector = DriftDetector(method="ks_test", alpha=0.05)
    detector.fit(reference_data)

    res = detector.analyze(shifted_eval_data)

    assert res.status == ReliabilityStatus.AVAILABLE
    assert res.drift_detected
    assert res.aggregate_drift_score > 0.5


def test_drift_feature_level_outputs(reference_data, shifted_eval_data):
    detector = DriftDetector(method="ks_test", alpha=0.05)
    detector.fit(reference_data, feature_names=["f1", "f2", "f3", "f4"])

    res = detector.analyze(shifted_eval_data)

    assert set(res.feature_drift_flags.keys()) == {"f1", "f2", "f3", "f4"}
    assert set(res.feature_p_values.keys()) == {"f1", "f2", "f3", "f4"}
    assert set(res.feature_statistics.keys()) == {"f1", "f2", "f3", "f4"}


def test_drift_constant_feature_handling(reference_data):
    # Add a constant feature with zero variance
    ref_with_const = np.column_stack([reference_data, np.ones(200)])
    eval_with_const = np.column_stack([reference_data[:50], np.ones(50)])

    detector = DriftDetector(method="ks_test")
    detector.fit(ref_with_const, feature_names=["f1", "f2", "f3", "f4", "const_feat"])

    res = detector.analyze(eval_with_const)

    assert res.status == ReliabilityStatus.AVAILABLE
    assert not res.feature_drift_flags["const_feat"]
    assert any("constant or has near-zero variance" in w for w in res.warnings)


def test_drift_sequential_adwin():
    wrapper = ADWINWrapper(delta=0.002)
    wrapper.initialize_features(["f1", "f2"])

    # Stream 50 in-distribution samples followed by 50 shifted samples
    flags_list = []
    for _ in range(50):
        flags = wrapper.update_sample({"f1": np.random.normal(0, 1), "f2": np.random.normal(0, 1)})
        flags_list.append(flags)

    for _ in range(50):
        flags = wrapper.update_sample({"f1": np.random.normal(10, 1), "f2": np.random.normal(10, 1)})
        flags_list.append(flags)

    assert len(flags_list) == 100


def test_drift_input_copy_safety(reference_data):
    df_eval = pd.DataFrame(reference_data[:20], columns=["f1", "f2", "f3", "f4"])
    df_eval_copy = df_eval.copy(deep=True)

    detector = DriftDetector(method="ks_test")
    detector.fit(reference_data)
    _ = detector.analyze(df_eval)

    # Assert evaluation DataFrame was not mutated
    pd.testing.assert_frame_equal(df_eval, df_eval_copy)


def test_drift_psi_method(reference_data, shifted_eval_data):
    detector = DriftDetector(method="psi")
    detector.fit(reference_data)

    res = detector.analyze(shifted_eval_data)
    assert res.status == ReliabilityStatus.AVAILABLE
    assert res.method == "psi"
    assert res.aggregate_drift_score > 0.0
