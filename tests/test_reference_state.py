"""
Unit tests for AEGIS-X ReferenceState and FeaturePreprocessor modules.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.core.exceptions import DatasetValidationError
from aegis.core.preprocessing import FeaturePreprocessor
from aegis.core.reference_state import ReferenceState


def test_feature_preprocessor_fitting_and_transform():
    ref_df = pd.DataFrame({"f1": [1.0, 2.0, 3.0, 4.0, 5.0], "f2": [10.0, 20.0, 30.0, 40.0, 50.0]})
    eval_df = pd.DataFrame({"f1": [2.0, 4.0], "f2": [20.0, 40.0]})

    preprocessor = FeaturePreprocessor(feature_names=["f1", "f2"])
    scaled_ref = preprocessor.fit_transform(ref_df)

    assert preprocessor.is_fitted
    assert scaled_ref.shape == (5, 2)
    assert np.allclose(np.mean(scaled_ref, axis=0), [0.0, 0.0])

    scaled_eval = preprocessor.transform(eval_df)
    assert scaled_eval.shape == (2, 2)


def test_feature_preprocessor_input_copy_safety():
    original_df = pd.DataFrame({"f1": [1.0, 2.0, 3.0], "f2": [10.0, 20.0, 30.0]})
    copy_df = original_df.copy(deep=True)

    preprocessor = FeaturePreprocessor()
    _ = preprocessor.fit_transform(original_df)

    # Assert original DataFrame was not mutated
    pd.testing.assert_frame_equal(original_df, copy_df)


def test_reference_state_computation():
    np.random.seed(42)
    ref_data = np.random.normal(loc=0.0, scale=1.0, size=(100, 3))

    ref_state = ReferenceState(feature_names=["f1", "f2", "f3"])
    ref_state.fit(ref_data)

    assert ref_state.is_fitted
    assert ref_state.num_samples == 100
    assert ref_state.num_features == 3
    assert ref_state.mean_vector.shape == (3,)
    assert ref_state.cov_matrix.shape == (3, 3)
    assert ref_state.inv_cov_matrix.shape == (3, 3)


def test_reference_state_empirical_percentiles():
    ref_state = ReferenceState(feature_names=["f1"])
    ref_state.register_empirical_distribution("test_score", np.array([1.0, 2.0, 3.0, 4.0, 5.0]))

    pct_low = ref_state.get_empirical_percentile("test_score", 0.5)
    pct_mid = ref_state.get_empirical_percentile("test_score", 3.0)
    pct_high = ref_state.get_empirical_percentile("test_score", 6.0)

    assert pct_low == 0.0
    assert pct_mid == 0.6  # 3 elements <= 3.0 out of 5 -> 3/5 = 0.6
    assert pct_high == 1.0


def test_reference_state_insufficient_samples():
    ref_state = ReferenceState()
    with pytest.raises(DatasetValidationError):
        ref_state.fit(np.array([[1.0, 2.0]]))
