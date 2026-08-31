"""
AEGIS-X Research Dataset Loaders for Module 12 Cross-Domain Validation.

Provides Breast Cancer Wisconsin and Digits Parity research validation fixtures.
"""

from typing import Tuple
import pandas as pd
from sklearn.datasets import load_breast_cancer, load_digits


def load_breast_cancer_fixture() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Loads Breast Cancer Wisconsin binary classification dataset.
    Returns: (X_features, y_target)
    """
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=[f"feature_{col}" for col in data.feature_names])
    y = pd.Series(data.target, name="target")
    return X, y


def load_digits_parity_fixture() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Loads Digits dataset transformed into binary Even (1) vs Odd (0) classification.
    CRITICAL: Original digit class identity (0..9) is used ONLY to derive parity target y,
    and is NEVER included in feature DataFrame X to prevent target leakage.
    """
    digits = load_digits()
    feature_cols = [f"pixel_{i}" for i in range(digits.data.shape[1])]
    X = pd.DataFrame(digits.data, columns=feature_cols)

    # Parity target: 1 for Even digits (0, 2, 4, 6, 8), 0 for Odd digits (1, 3, 5, 7, 9)
    y = pd.Series((digits.target % 2 == 0).astype(int), name="parity_target")

    return X, y
