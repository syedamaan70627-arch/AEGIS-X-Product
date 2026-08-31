"""
Unit tests for AEGIS-X Research Dataset Loaders (Module 12).
"""

import numpy as np
import pandas as pd
import pytest

from aegis.evaluation.datasets import load_breast_cancer_fixture, load_digits_parity_fixture


def test_load_breast_cancer_fixture():
    X, y = load_breast_cancer_fixture()

    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert X.shape[0] == 569
    assert X.shape[1] == 30
    assert set(np.unique(y)) == {0, 1}


def test_load_digits_parity_fixture_prevents_target_leakage():
    X, y = load_digits_parity_fixture()

    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert X.shape[0] == 1797
    assert X.shape[1] == 64
    assert set(np.unique(y)) == {0, 1}

    # CRITICAL LEAKAGE PREVENTION TEST:
    # Original digit identity must NOT be present in feature columns
    assert "target" not in X.columns
    assert "digit" not in X.columns
    assert "parity_target" not in X.columns
