"""
Unit tests for AEGIS-X Real Cross-Domain Validation Engine (Module 12).
"""

import numpy as np
import pandas as pd
import pytest

from aegis.core.contracts import ReliabilityStatus
from aegis.evaluation.cross_domain import CrossDomainEvaluator
from aegis.evaluation.datasets import load_breast_cancer_fixture, load_digits_parity_fixture


def test_cross_domain_single_domain_evaluation():
    X_bc, y_bc = load_breast_cancer_fixture()

    res = CrossDomainEvaluator.evaluate_domain("Breast Cancer Wisconsin", X_bc, y_bc, random_state=42)

    assert res.domain_name == "Breast Cancer Wisconsin"
    assert res.sample_count == 569
    assert res.feature_count == 30
    assert 0.0 <= res.baseline_accuracy <= 1.0
    assert 0.0 <= res.fusion_auroc <= 1.0
    assert res.best_individual_signal in ["OOD", "Uncertainty", "Drift"]
    assert -1.0 <= res.spearman_correlation <= 1.0
    assert 0.0 <= res.unseen_family_auroc <= 1.0


def test_cross_domain_evaluate_all_domains():
    res = CrossDomainEvaluator.evaluate_all_domains(random_state=42)

    assert res.status == ReliabilityStatus.AVAILABLE
    assert res.total_domains == 2
    assert "Breast Cancer Wisconsin" in res.domain_results
    assert "Digits Parity (Even vs Odd)" in res.domain_results

    assert 0.0 <= res.mean_fusion_auroc <= 1.0
    assert -1.0 <= res.mean_spearman_correlation <= 1.0
    assert 0.0 <= res.mean_unseen_family_auroc <= 1.0
    assert 0 <= res.fusion_win_count <= 2


def test_cross_domain_input_copy_safety():
    X_dig, y_dig = load_digits_parity_fixture()
    X_orig = X_dig.copy(deep=True)

    CrossDomainEvaluator.evaluate_domain("Digits Parity (Even vs Odd)", X_dig, y_dig, random_state=42)

    # Source DataFrames must remain unmutated
    pd.testing.assert_frame_equal(X_dig, X_orig)
