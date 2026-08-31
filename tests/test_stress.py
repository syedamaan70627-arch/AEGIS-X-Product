"""
Unit tests for AEGIS-X Controlled Stress testing and corruptions module.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.core.exceptions import DatasetValidationError
from aegis.stress.corruptions import (
    combined_stress,
    feature_dropout_stress,
    feature_permutation_stress,
    gaussian_noise_stress,
)
from aegis.stress.engine import ControlledStressEngine


@pytest.fixture
def sample_features():
    np.random.seed(42)
    return pd.DataFrame(
        np.random.normal(loc=10.0, scale=2.0, size=(50, 4)),
        columns=["f1", "f2", "f3", "f4"],
    )


def test_gaussian_noise_stress(sample_features):
    copy_orig = sample_features.copy(deep=True)
    stressed = gaussian_noise_stress(sample_features, severity=0.3, seed=42)

    # Source data must remain unmutated
    pd.testing.assert_frame_equal(sample_features, copy_orig)
    # Stressed data shape must equal original
    assert stressed.shape == sample_features.shape
    # Values must differ due to noise
    assert not np.allclose(stressed.to_numpy(), sample_features.to_numpy())


def test_feature_dropout_stress(sample_features):
    copy_orig = sample_features.copy(deep=True)
    stressed = feature_dropout_stress(sample_features, severity=0.5, seed=42)

    pd.testing.assert_frame_equal(sample_features, copy_orig)
    # At least some values should be zeroed out
    num_zeros = np.sum(stressed.to_numpy() == 0.0)
    assert num_zeros > 0


def test_feature_permutation_stress(sample_features):
    copy_orig = sample_features.copy(deep=True)
    stressed = feature_permutation_stress(sample_features, severity=0.5, seed=42)

    pd.testing.assert_frame_equal(sample_features, copy_orig)
    assert stressed.shape == sample_features.shape


def test_combined_stress(sample_features):
    stressed = combined_stress(sample_features, severity=0.4, seed=42)
    assert stressed.shape == sample_features.shape


def test_stress_invalid_severity(sample_features):
    with pytest.raises(DatasetValidationError):
        gaussian_noise_stress(sample_features, severity=-0.1)

    with pytest.raises(DatasetValidationError):
        feature_dropout_stress(sample_features, severity=1.5)


def test_stress_engine_run(sample_features):
    engine = ControlledStressEngine(random_state=42)
    res = engine.run_stress_test(
        evaluation_data=sample_features,
        stress_type="Gaussian_Noise",
        severity=0.3,
    )

    assert res.status.value == "AVAILABLE"
    assert res.stress_type == "Gaussian_Noise"
    assert res.severity == 0.3
