"""
Unit tests for Temporal Safety and Feature Leakage Prevention in Failure Prediction.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.prediction.features import PredictionFeatureBuilder


def test_delta_features_use_backward_looking_diff():
    df = pd.DataFrame({
        "ood_risk": [0.1, 0.3, 0.7, 0.9],
        "uncertainty_risk": [0.2, 0.4, 0.5, 0.8],
        "drift_risk": [0.0, 0.1, 0.2, 0.4],
        "fused_risk": [0.15, 0.35, 0.6, 0.85],
    })

    feats_df, feat_names = PredictionFeatureBuilder.build_features(df, feature_set_type="dynamic")

    # Row 0 delta should be 0.0 (initial backward diff)
    assert feats_df.loc[0, "delta_ood_risk"] == 0.0

    # Row 1 delta must equal f_1 - f_0 = 0.3 - 0.1 = 0.2
    np.testing.assert_allclose(feats_df.loc[1, "delta_ood_risk"], 0.2)

    # Row 2 delta must equal f_2 - f_1 = 0.7 - 0.3 = 0.4
    np.testing.assert_allclose(feats_df.loc[2, "delta_ood_risk"], 0.4)


test_df = pd.DataFrame({
    "ood_risk": [0.1, 0.3, 0.7],
    "uncertainty_risk": [0.2, 0.4, 0.5],
    "drift_risk": [0.0, 0.1, 0.2],
    "fused_risk": [0.15, 0.35, 0.6],
    "severity": [0.1, 0.2, 0.3],  # Controlled experiment variable
    "future_target_label": [0, 1, 1],  # Ground truth label
})


def test_severity_and_future_labels_excluded_from_predictors():
    feats_df, feat_names = PredictionFeatureBuilder.build_features(test_df, feature_set_type="dynamic")

    assert "severity" not in feat_names
    assert "future_target_label" not in feat_names
    assert "severity" not in feats_df.columns
    assert "future_target_label" not in feats_df.columns
