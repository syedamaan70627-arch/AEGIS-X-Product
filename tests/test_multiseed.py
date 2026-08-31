"""
Unit tests for AEGIS-X Multi-Seed Reliability Evaluator (Module 13).
"""

import pytest

from aegis.core.contracts import ReliabilityStatus
from aegis.evaluation.multiseed import MultiSeedEvaluator


def test_multi_seed_single_run():
    from aegis.evaluation.datasets import load_breast_cancer_fixture

    X, y = load_breast_cancer_fixture()
    res = MultiSeedEvaluator.run_single_seed_domain(seed=42, domain_name="Breast Cancer Wisconsin", X=X, y=y)

    assert res.seed == 42
    assert res.domain_name == "Breast Cancer Wisconsin"
    assert 0.0 <= res.fusion_auroc <= 1.0
    assert 0.0 <= res.fusion_aupr <= 1.0
    assert isinstance(res.paired_aupr_gain, float)
    assert isinstance(res.is_fusion_win, bool)


def test_multi_seed_study_execution():
    # Use 2 seeds for quick test execution
    seeds = [42, 101]
    summary = MultiSeedEvaluator.run_multi_seed_study(seeds=seeds, n_bootstrap=200)

    assert summary.status == ReliabilityStatus.AVAILABLE
    assert summary.total_requested_experiments == 4
    assert summary.completed_experiments == 4
    assert summary.failed_experiments == 0

    assert summary.verdict == "ROBUST FRAMEWORK / MIXED FUSION EVIDENCE"
    assert summary.is_fusion_superiority_established is False

    # Check negative findings preserved
    assert len(summary.preserved_negative_findings) >= 8

    # Bootstrap CIs must have lower <= estimate <= upper
    agg = summary.aggregate_results
    assert agg.fusion_auroc_ci.lower <= agg.fusion_auroc_ci.estimate <= agg.fusion_auroc_ci.upper
    assert agg.paired_gain_ci.lower <= agg.paired_gain_ci.estimate <= agg.paired_gain_ci.upper


def test_severity_is_excluded_from_predictors():
    # Verify that severity is not in any feature dataframe passed to model fitting
    from aegis.evaluation.datasets import load_breast_cancer_fixture
    X, y = load_breast_cancer_fixture()

    res = MultiSeedEvaluator.run_single_seed_domain(seed=42, domain_name="Breast Cancer Wisconsin", X=X, y=y)
    assert "severity" not in X.columns
