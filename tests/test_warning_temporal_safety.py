"""
Unit tests for Temporal Safety in Early Warning Engine.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.warning.features import EarlyWarningFeatureBuilder


def test_early_warning_backward_looking_deltas():
    df = pd.DataFrame({
        "ood_risk": [0.2, 0.4, 0.6],
        "uncertainty_risk": [0.1, 0.3, 0.5],
        "drift_risk": [0.0, 0.1, 0.2],
        "fused_risk": [0.15, 0.35, 0.55],
    })

    feats_df, feat_names = EarlyWarningFeatureBuilder.build_features(df)

    # Initial delta at index 0 must be 0.0
    assert feats_df.loc[0, "delta_ood_risk"] == 0.0

    # Index 1 delta must equal f_1 - f_0 = 0.4 - 0.2 = 0.2
    np.testing.assert_allclose(feats_df.loc[1, "delta_ood_risk"], 0.2)


def test_severity_and_future_labels_excluded():
    df = pd.DataFrame({
        "ood_risk": [0.2, 0.4],
        "uncertainty_risk": [0.1, 0.3],
        "drift_risk": [0.0, 0.1],
        "fused_risk": [0.15, 0.35],
        "severity": [0.1, 0.2],
        "future_label": [1, 1],
    })

    feats_df, feat_names = EarlyWarningFeatureBuilder.build_features(df)

    assert "severity" not in feat_names
    assert "future_label" not in feat_names
