"""
Unit tests for AEGIS-X Structured Fault Transformations Module.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.core.exceptions import DatasetValidationError
from aegis.faults.transformations import (
    FaultInjector,
    inject_channel_swap,
    inject_feature_bias,
    inject_gain_error,
    inject_sign_inversion,
    inject_stuck_at,
)


@pytest.fixture
def sample_features():
    np.random.seed(42)
    return pd.DataFrame(
        np.random.normal(loc=5.0, scale=1.5, size=(40, 4)),
        columns=["feat_a", "feat_b", "feat_c", "feat_d"],
    )


def test_inject_feature_bias_copy_safety(sample_features):
    orig_copy = sample_features.copy(deep=True)
    faulted = inject_feature_bias(sample_features, severity=0.5, seed=42)

    # Source data must remain unmutated
    pd.testing.assert_frame_equal(sample_features, orig_copy)
    assert faulted.shape == sample_features.shape
    assert not np.allclose(faulted.to_numpy(), sample_features.to_numpy())


def test_inject_gain_error(sample_features):
    orig_copy = sample_features.copy(deep=True)
    faulted = inject_gain_error(sample_features, severity=0.3, seed=42)

    pd.testing.assert_frame_equal(sample_features, orig_copy)
    assert faulted.shape == sample_features.shape


def test_inject_stuck_at(sample_features):
    orig_copy = sample_features.copy(deep=True)
    faulted = inject_stuck_at(sample_features, severity=0.6, stuck_value=0.0, seed=42)

    pd.testing.assert_frame_equal(sample_features, orig_copy)
    num_zeros = np.sum(faulted.to_numpy() == 0.0)
    assert num_zeros > 0


def test_inject_channel_swap(sample_features):
    orig_copy = sample_features.copy(deep=True)
    faulted = inject_channel_swap(sample_features, severity=0.5, seed=42)

    pd.testing.assert_frame_equal(sample_features, orig_copy)
    # Feature column names must be preserved
    assert list(faulted.columns) == list(sample_features.columns)


def test_inject_sign_inversion(sample_features):
    orig_copy = sample_features.copy(deep=True)
    faulted = inject_sign_inversion(sample_features, severity=0.5, seed=42)

    pd.testing.assert_frame_equal(sample_features, orig_copy)
    assert faulted.shape == sample_features.shape


def test_fault_injector_unified_engine(sample_features):
    faulted, res = FaultInjector.inject(
        sample_features,
        fault_type="Sensor_Bias",
        severity=0.4,
        seed=42,
    )

    assert res.status.value == "AVAILABLE"
    assert res.fault_type == "Sensor_Bias"
    assert res.severity == 0.4
    assert res.original_shape == (40, 4)
    assert res.transformed_shape == (40, 4)


def test_invalid_severity(sample_features):
    with pytest.raises(DatasetValidationError):
        inject_feature_bias(sample_features, severity=-0.1)

    with pytest.raises(DatasetValidationError):
        inject_gain_error(sample_features, severity=1.2)


def test_invalid_fault_type(sample_features):
    with pytest.raises(DatasetValidationError):
        FaultInjector.inject(sample_features, fault_type="Invalid_Fault_Type", severity=0.3)
