"""
Unit tests for AEGIS-X Bootstrap Confidence Interval Module (Module 13).
"""

import numpy as np
import pytest

from aegis.evaluation.bootstrap import bootstrap_mean_ci


def test_bootstrap_mean_ci_bounds():
    data = np.array([0.75, 0.78, 0.80, 0.82, 0.85, 0.79, 0.77, 0.81, 0.83, 0.76])

    res = bootstrap_mean_ci(data, n_bootstrap=500, ci=0.95, seed=42)

    assert isinstance(res.estimate, float)
    assert isinstance(res.lower, float)
    assert isinstance(res.upper, float)

    # lower <= estimate <= upper
    assert res.lower <= res.estimate <= res.upper
    assert res.confidence_level == 0.95


def test_bootstrap_mean_ci_determinism():
    data = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

    res1 = bootstrap_mean_ci(data, n_bootstrap=200, seed=42)
    res2 = bootstrap_mean_ci(data, n_bootstrap=200, seed=42)

    assert res1.estimate == res2.estimate
    assert res1.lower == res2.lower
    assert res1.upper == res2.upper
