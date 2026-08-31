"""
Unit tests for AEGIS-X Failure Predictor and Feature Builder.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.core.contracts import ReliabilityStatus
from aegis.prediction.engine import FailurePredictor
from aegis.prediction.features import PredictionFeatureBuilder


@pytest.fixture
def sample_prediction_data():
    np.random.seed(42)
    n = 60
    ood = np.random.uniform(0.1, 0.9, n)
    unc = np.random.uniform(0.1, 0.9, n)
    drift = np.random.uniform(0.0, 0.5, n)
    fused = (ood * 0.4 + unc * 0.4 + drift * 0.2)

    # Failure onset target (binary transition indicator)
    onset_target = np.array([1 if (i % 4 == 0) else 0 for i in range(n)])

    df = pd.DataFrame({
        "ood_risk": ood,
        "uncertainty_risk": unc,
        "drift_risk": drift,
        "fused_risk": fused,
        "Failure_Onset_Next": onset_target,
    })

    train_df = df.iloc[:25].copy()
    val_df = df.iloc[25:45].copy()
    test_df = df.iloc[45:].copy()

    return train_df, val_df, test_df


def test_prediction_feature_builder(sample_prediction_data):
    train_df, _, _ = sample_prediction_data
    orig_copy = train_df.copy(deep=True)

    feats_df, feat_names = PredictionFeatureBuilder.build_features(train_df, feature_set_type="dynamic")

    # Source data must remain unmutated
    pd.testing.assert_frame_equal(train_df, orig_copy)
    assert len(feat_names) == 8
    assert "delta_ood_risk" in feat_names
    assert "severity" not in feat_names


def test_failure_predictor_fit_and_predict(sample_prediction_data):
    train_df, val_df, test_df = sample_prediction_data

    predictor = FailurePredictor(feature_set_type="dynamic", random_state=42)
    fit_res = predictor.fit(train_df, val_df)

    assert fit_res.status == ReliabilityStatus.AVAILABLE
    assert predictor.is_fitted
    assert predictor.threshold_info is not None
    assert predictor.threshold_info.selection_split == "validation"

    # Execute prediction on test split
    pred_res = predictor.predict(test_df)
    assert pred_res.status == ReliabilityStatus.AVAILABLE
    assert len(pred_res.predictions) == len(test_df)
    assert 0.0 <= pred_res.mean_predicted_probability <= 1.0


def test_unfitted_predictor_returns_not_available(sample_prediction_data):
    _, _, test_df = sample_prediction_data
    unfitted_predictor = FailurePredictor()

    res = unfitted_predictor.predict(test_df)
    assert res.status == ReliabilityStatus.NOT_AVAILABLE
    assert any("not fitted" in w for w in res.warnings)


def test_predictor_serialization(sample_prediction_data, tmp_path):
    train_df, val_df, test_df = sample_prediction_data

    predictor = FailurePredictor(feature_set_type="dynamic", random_state=42)
    predictor.fit(train_df, val_df)

    save_dir = tmp_path / "predictor_artifact"
    predictor.save_artifact(save_dir)

    loaded_predictor = FailurePredictor().load_artifact(save_dir)
    assert loaded_predictor.is_fitted
    assert loaded_predictor.threshold_info.threshold == predictor.threshold_info.threshold

    res1 = predictor.predict(test_df)
    res2 = loaded_predictor.predict(test_df)

    np.testing.assert_allclose(res1.mean_predicted_probability, res2.mean_predicted_probability)
