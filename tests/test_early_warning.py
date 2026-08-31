"""
Unit tests for AEGIS-X Early Warning Engine and Feature Builder.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.core.contracts import ReliabilityStatus
from aegis.warning.engine import EarlyWarningEngine
from aegis.warning.features import EarlyWarningFeatureBuilder


@pytest.fixture
def sample_warning_data():
    np.random.seed(42)
    n = 60
    ood = np.random.uniform(0.1, 0.9, n)
    unc = np.random.uniform(0.1, 0.9, n)
    drift = np.random.uniform(0.0, 0.5, n)
    fused = (ood * 0.4 + unc * 0.4 + drift * 0.2)

    df = pd.DataFrame({
        "ood_risk": ood,
        "uncertainty_risk": unc,
        "drift_risk": drift,
        "fused_risk": fused,
        "Failure_Within_3": np.array([1 if (i % 3 == 0) else 0 for i in range(n)]),
        "Failure_Rate": np.array([0.15 if (i > 40) else 0.02 for i in range(n)]),
        "trajectory_id": np.repeat(np.arange(6), 10),
    })

    train_df = df.iloc[:25].copy()
    val_df = df.iloc[25:45].copy()
    test_df = df.iloc[45:].copy()

    return train_df, val_df, test_df


def test_early_warning_feature_builder(sample_warning_data):
    train_df, _, _ = sample_warning_data
    orig_copy = train_df.copy(deep=True)

    feats_df, feat_names = EarlyWarningFeatureBuilder.build_features(train_df)

    pd.testing.assert_frame_equal(train_df, orig_copy)
    assert len(feat_names) == 8
    assert "delta_fused_risk" in feat_names
    assert "severity" not in feat_names


def test_early_warning_fit_and_predict(sample_warning_data):
    train_df, val_df, test_df = sample_warning_data

    engine = EarlyWarningEngine(horizon_val=3, random_state=42)
    eval_res = engine.fit(train_df, val_df)

    assert eval_res.status == ReliabilityStatus.AVAILABLE
    assert engine.is_fitted
    assert engine.horizon.unit == "controlled_degradation_states"

    res = engine.predict_warning(test_df)
    assert res.status == ReliabilityStatus.AVAILABLE
    assert 0.0 <= res.warning_score <= 1.0


def test_unfitted_early_warning_returns_not_available(sample_warning_data):
    _, _, test_df = sample_warning_data
    engine = EarlyWarningEngine()

    res = engine.predict_warning(test_df)
    assert res.status == ReliabilityStatus.NOT_AVAILABLE
    assert any("not fitted" in w for w in res.warnings)


def test_early_warning_serialization(sample_warning_data, tmp_path):
    train_df, val_df, test_df = sample_warning_data

    engine = EarlyWarningEngine(horizon_val=3, random_state=42)
    engine.fit(train_df, val_df)

    save_dir = tmp_path / "warning_artifact"
    engine.save_artifact(save_dir)

    loaded_engine = EarlyWarningEngine().load_artifact(save_dir)
    assert loaded_engine.is_fitted
    assert loaded_engine.warning_threshold == engine.warning_threshold

    res1 = engine.predict_warning(test_df)
    res2 = loaded_engine.predict_warning(test_df)
    np.testing.assert_allclose(res1.warning_score, res2.warning_score)
