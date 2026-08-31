"""
Unit tests for AEGIS-X StressRobustFusion and group-aware leakage prevention.
"""

import numpy as np
import pytest

from aegis.core.exceptions import DatasetValidationError
from aegis.fusion.engine import OriginalFusion, StressRobustFusion


def test_stress_robust_fusion_group_aware_split():
    np.random.seed(42)
    s_ood = np.random.uniform(0.0, 1.0, 100)
    u = np.random.uniform(0.0, 1.0, 100)
    d = np.random.uniform(0.0, 1.0, 100)
    y_target = (s_ood * 0.4 + u * 0.5 + d * 0.3 > 0.6).astype(int)

    # 10 groups representing 10 stress perturbation runs
    sample_groups = np.repeat(np.arange(10), 10)

    robust_fusion = StressRobustFusion(random_state=42)
    robust_fusion.fit_with_group_split(
        s_ood, u, d, y_target, sample_groups=sample_groups
    )

    assert robust_fusion.is_fitted

    res = robust_fusion.fuse(s_ood[:10], u[:10], d[:10])
    assert res.status.value == "AVAILABLE"
    assert len(res.fused_risk_scores) == 10


def test_stress_robust_fusion_insufficient_groups():
    s_ood = np.array([0.1, 0.2, 0.3])
    u = np.array([0.1, 0.2, 0.3])
    d = np.array([0.1, 0.2, 0.3])
    y_target = np.array([0, 0, 1])
    sample_groups = np.array([1, 1, 1])  # Only 1 unique group

    robust_fusion = StressRobustFusion()
    with pytest.raises(DatasetValidationError):
        robust_fusion.fit_with_group_split(s_ood, u, d, y_target, sample_groups=sample_groups)


def test_original_fusion_negative_result_warning():
    orig_fusion = OriginalFusion()
    res = orig_fusion.fuse(np.array([0.1]), np.array([0.2]), np.array([0.0]))

    assert res.status.value == "AVAILABLE"
    assert any("Module 6 negative result" in w for w in res.warnings)
