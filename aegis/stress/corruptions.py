"""
AEGIS-X Controlled Stress Corruptions Module.

Migrates Module 6 stress corruption generators: Gaussian noise, feature dropout,
feature permutation, and combined stress while enforcing strict input-copy safety.
"""

from typing import List, Tuple, Union
import numpy as np
import pandas as pd

from aegis.core.exceptions import DatasetValidationError


def _ensure_copy(data: Union[pd.DataFrame, np.ndarray]) -> Tuple[Union[pd.DataFrame, np.ndarray], bool]:
    if isinstance(data, pd.DataFrame):
        return data.copy(deep=True), True
    elif isinstance(data, np.ndarray):
        return np.array(data, copy=True), False
    else:
        raise DatasetValidationError(f"Unsupported data type for stress testing: {type(data)}")


def validate_severity(severity: float) -> None:
    if not (0.0 <= severity <= 1.0):
        raise DatasetValidationError(f"Stress severity must be in range [0.0, 1.0], got {severity}.")


def gaussian_noise_stress(
    data: Union[pd.DataFrame, np.ndarray],
    severity: float,
    seed: int = 42,
) -> Union[pd.DataFrame, np.ndarray]:
    """Applies Gaussian noise stress scaling by column standard deviation to a data copy."""
    validate_severity(severity)
    if severity == 0.0:
        return data.copy(deep=True) if isinstance(data, pd.DataFrame) else np.array(data, copy=True)

    stressed_data, is_df = _ensure_copy(data)
    rng = np.random.default_rng(seed)

    if is_df:
        for col in stressed_data.columns:
            std = float(stressed_data[col].std())
            if std < 1e-12:
                std = 1.0
            noise = rng.normal(loc=0.0, scale=severity * std, size=len(stressed_data))
            stressed_data[col] = stressed_data[col] + noise
    else:
        stds = np.std(stressed_data, axis=0)
        stds = np.where(stds < 1e-12, 1.0, stds)
        noise = rng.normal(loc=0.0, scale=severity * stds, size=stressed_data.shape)
        stressed_data = stressed_data + noise

    return stressed_data


def feature_dropout_stress(
    data: Union[pd.DataFrame, np.ndarray],
    severity: float,
    seed: int = 42,
) -> Union[pd.DataFrame, np.ndarray]:
    """Randomly zeros out a fraction equal to severity of feature values in a data copy."""
    validate_severity(severity)
    if severity == 0.0:
        return data.copy(deep=True) if isinstance(data, pd.DataFrame) else np.array(data, copy=True)

    stressed_data, is_df = _ensure_copy(data)
    rng = np.random.default_rng(seed)

    if is_df:
        vals = stressed_data.to_numpy(copy=True)
        mask = rng.uniform(low=0.0, high=1.0, size=vals.shape) < severity
        vals[mask] = 0.0
        stressed_data = pd.DataFrame(vals, columns=data.columns, index=data.index)
    else:
        mask = rng.uniform(low=0.0, high=1.0, size=stressed_data.shape) < severity
        stressed_data[mask] = 0.0

    return stressed_data


def feature_permutation_stress(
    data: Union[pd.DataFrame, np.ndarray],
    severity: float,
    seed: int = 42,
) -> Union[pd.DataFrame, np.ndarray]:
    """Randomly permutes feature values across rows for a fraction equal to severity in a data copy."""
    validate_severity(severity)
    if severity == 0.0:
        return data.copy(deep=True) if isinstance(data, pd.DataFrame) else np.array(data, copy=True)

    stressed_data, is_df = _ensure_copy(data)
    rng = np.random.default_rng(seed)
    n_samples = len(data)

    if is_df:
        n_perm = int(np.ceil(n_samples * severity))
        for col in stressed_data.columns:
            perm_indices = rng.choice(n_samples, size=n_perm, replace=False)
            shuffled = stressed_data[col].iloc[perm_indices].to_numpy(copy=True)
            rng.shuffle(shuffled)
            stressed_data.iloc[perm_indices, stressed_data.columns.get_loc(col)] = shuffled
    else:
        n_features = stressed_data.shape[1]
        n_perm = int(np.ceil(n_samples * severity))
        for j in range(n_features):
            perm_indices = rng.choice(n_samples, size=n_perm, replace=False)
            shuffled = stressed_data[perm_indices, j].copy()
            rng.shuffle(shuffled)
            stressed_data[perm_indices, j] = shuffled

    return stressed_data


def combined_stress(
    data: Union[pd.DataFrame, np.ndarray],
    severity: float,
    seed: int = 42,
) -> Union[pd.DataFrame, np.ndarray]:
    """Sequentially applies Gaussian noise, feature dropout, and feature permutation to a data copy."""
    validate_severity(severity)
    if severity == 0.0:
        return data.copy(deep=True) if isinstance(data, pd.DataFrame) else np.array(data, copy=True)

    # Divide severity across the 3 corruptions for stability
    sub_sev = severity * 0.5
    s1 = gaussian_noise_stress(data, sub_sev, seed=seed)
    s2 = feature_dropout_stress(s1, sub_sev, seed=seed + 1)
    s3 = feature_permutation_stress(s2, sub_sev, seed=seed + 2)
    return s3
