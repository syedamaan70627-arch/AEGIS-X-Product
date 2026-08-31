"""
Unit tests for AEGIS-X Fusion Engine (OriginalFusion and StressRobustFusion) modules.
"""

import numpy as np
import pytest

from aegis.core.contracts import ReliabilityStatus
from aegis.fusion.engine import OriginalFusion, StressRobustFusion
from aegis.fusion.features import FusionFeatureTransformer


def test_fusion_feature_transformer():
    s_ood = np.array([0.1, 0.5, 0.9])
    u = np.array([0.2, 0.4, 0.8])
    d = np.array([0.0, 0.3, 0.7])

    feats = FusionFeatureTransformer.transform_signals(s_ood, u, d)

    assert feats.shape == (3, 7)
    # Check interaction terms
    np.testing.assert_allclose(feats[0, 3], 0.1 * 0.2)  # OOD * U
    np.testing.assert_allclose(feats[0, 4], 0.1 * 0.0)  # OOD * D
    np.testing.assert_allclose(feats[0, 5], 0.2 * 0.0)  # U * D
    np.testing.assert_allclose(feats[0, 6], 0.1 * 0.2 * 0.0)  # OOD * U * D


def test_original_fusion_unfitted_and_fitted():
    s_ood = np.array([0.2, 0.8])
    u = np.array([0.1, 0.7])
    d = np.array([0.0, 0.5])

    fusion = OriginalFusion()
    res_unfitted = fusion.fuse(s_ood, u, d)

    assert res_unfitted.status == ReliabilityStatus.AVAILABLE
    assert res_unfitted.method == "OriginalFusion"
    assert len(res_unfitted.fused_risk_scores) == 2
    assert res_unfitted.fused_risk_scores[1] > res_unfitted.fused_risk_scores[0]

    # Individual signals remain accessible
    np.testing.assert_allclose(res_unfitted.ood_signal, s_ood)
    np.testing.assert_allclose(res_unfitted.uncertainty_signal, u)

    # Fit fusion model
    y_target = np.array([0.0, 1.0])
    fusion.fit(s_ood, u, d, y_target)
    assert fusion.is_fitted

    res_fitted = fusion.fuse(s_ood, u, d)
    assert res_fitted.status == ReliabilityStatus.AVAILABLE
    assert res_fitted.model_metadata["is_fitted"]


def test_stress_robust_fusion_fit_and_fuse():
    np.random.seed(42)
    s_ood = np.random.uniform(0, 1, 50)
    u = np.random.uniform(0, 1, 50)
    d = np.random.uniform(0, 1, 50)
    y_target = (s_ood + u + d > 1.2).astype(int)
    groups = np.repeat(np.arange(10), 5)  # 10 base sample groups

    robust_fusion = StressRobustFusion(random_state=42)
    robust_fusion.fit_with_group_split(s_ood, u, d, y_target, sample_groups=groups)

    assert robust_fusion.is_fitted

    eval_res = robust_fusion.fuse(s_ood[:10], u[:10], d[:10])
    assert eval_res.status == ReliabilityStatus.AVAILABLE
    assert eval_res.method == "StressRobustFusion"
    assert len(eval_res.fused_risk_scores) == 10
    assert 0.0 <= eval_res.aggregate_fused_risk <= 1.0


def test_fusion_missing_inputs():
    fusion = OriginalFusion()
    res = fusion.fuse(None, np.array([0.5]), np.array([0.1]))

    assert res.status == ReliabilityStatus.NOT_AVAILABLE
    assert any("Missing input" in w for w in res.warnings)


def test_fusion_deterministic_inference():
    s_ood = np.array([0.3, 0.6])
    u = np.array([0.2, 0.5])
    d = np.array([0.1, 0.4])

    fusion = OriginalFusion()
    res1 = fusion.fuse(s_ood, u, d)
    res2 = fusion.fuse(s_ood, u, d)

    np.testing.assert_allclose(res1.fused_risk_scores, res2.fused_risk_scores)
