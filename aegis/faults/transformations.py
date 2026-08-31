"""
AEGIS-X Structured Fault Transformations Module.

Migrates Module 7 fault injection families: Feature Bias, Gain Error, Stuck-At,
Channel Swap, and Sign Inversion with strict input-copy safety and determinism.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from aegis.core.contracts import FaultInjectionResult, FaultType, ReliabilityStatus
from aegis.core.exceptions import DatasetValidationError


def _ensure_copy(data: Union[pd.DataFrame, np.ndarray]) -> Tuple[Union[pd.DataFrame, np.ndarray], bool]:
    if isinstance(data, pd.DataFrame):
        return data.copy(deep=True), True
    elif isinstance(data, np.ndarray):
        return np.array(data, copy=True), False
    else:
        raise DatasetValidationError(f"Unsupported data type for fault injection: {type(data)}")


def validate_severity(severity: float) -> None:
    if not (0.0 <= severity <= 1.0):
        raise DatasetValidationError(f"Fault severity must be in range [0.0, 1.0], got {severity}.")


def inject_feature_bias(
    data: Union[pd.DataFrame, np.ndarray],
    severity: float,
    feature_names: Optional[List[str]] = None,
    seed: int = 42,
) -> Union[pd.DataFrame, np.ndarray]:
    """Adds feature bias proportional to column mean/scale and severity to a data copy."""
    validate_severity(severity)
    if severity == 0.0:
        return data.copy(deep=True) if isinstance(data, pd.DataFrame) else np.array(data, copy=True)

    faulted_data, is_df = _ensure_copy(data)
    rng = np.random.default_rng(seed)

    if is_df:
        cols = feature_names if feature_names else list(faulted_data.columns[:2])
        for col in cols:
            if col in faulted_data.columns:
                mean_val = float(faulted_data[col].mean())
                std_val = float(faulted_data[col].std())
                bias = severity * (abs(mean_val) if abs(mean_val) > 1e-6 else (std_val if std_val > 1e-6 else 1.0))
                faulted_data[col] = faulted_data[col] + bias
    else:
        n_feat = faulted_data.shape[1]
        target_indices = rng.choice(n_feat, size=min(2, n_feat), replace=False)
        for idx in target_indices:
            mean_val = float(np.mean(faulted_data[:, idx]))
            std_val = float(np.std(faulted_data[:, idx]))
            bias = severity * (abs(mean_val) if abs(mean_val) > 1e-6 else (std_val if std_val > 1e-6 else 1.0))
            faulted_data[:, idx] = faulted_data[:, idx] + bias

    return faulted_data


def inject_gain_error(
    data: Union[pd.DataFrame, np.ndarray],
    severity: float,
    feature_names: Optional[List[str]] = None,
    seed: int = 42,
) -> Union[pd.DataFrame, np.ndarray]:
    """Multiplies feature values by a gain factor (1.0 + severity) in a data copy."""
    validate_severity(severity)
    if severity == 0.0:
        return data.copy(deep=True) if isinstance(data, pd.DataFrame) else np.array(data, copy=True)

    faulted_data, is_df = _ensure_copy(data)
    rng = np.random.default_rng(seed)
    gain_factor = 1.0 + severity * 2.0  # Scale gain factor with severity

    if is_df:
        cols = feature_names if feature_names else list(faulted_data.columns[:2])
        for col in cols:
            if col in faulted_data.columns:
                faulted_data[col] = faulted_data[col] * gain_factor
    else:
        n_feat = faulted_data.shape[1]
        target_indices = rng.choice(n_feat, size=min(2, n_feat), replace=False)
        for idx in target_indices:
            faulted_data[:, idx] = faulted_data[:, idx] * gain_factor

    return faulted_data


def inject_stuck_at(
    data: Union[pd.DataFrame, np.ndarray],
    severity: float,
    feature_names: Optional[List[str]] = None,
    stuck_value: Optional[float] = None,
    seed: int = 42,
) -> Union[pd.DataFrame, np.ndarray]:
    """Sets target feature values to a constant stuck value in a data copy."""
    validate_severity(severity)
    if severity == 0.0:
        return data.copy(deep=True) if isinstance(data, pd.DataFrame) else np.array(data, copy=True)

    faulted_data, is_df = _ensure_copy(data)
    rng = np.random.default_rng(seed)

    if is_df:
        cols = feature_names if feature_names else list(faulted_data.columns[:1])
        for col in cols:
            if col in faulted_data.columns:
                val = stuck_value if stuck_value is not None else float(faulted_data[col].mean())
                # Replace a fraction = severity of samples with stuck_val
                mask = rng.uniform(0, 1, size=len(faulted_data)) < severity
                faulted_data.loc[mask, col] = val
    else:
        n_samples, n_feat = faulted_data.shape
        target_indices = rng.choice(n_feat, size=min(1, n_feat), replace=False)
        for idx in target_indices:
            val = stuck_value if stuck_value is not None else float(np.mean(faulted_data[:, idx]))
            mask = rng.uniform(0, 1, size=n_samples) < severity
            faulted_data[mask, idx] = val

    return faulted_data


def inject_channel_swap(
    data: Union[pd.DataFrame, np.ndarray],
    severity: float,
    feature_pair: Optional[Tuple[str, str]] = None,
    seed: int = 42,
) -> Union[pd.DataFrame, np.ndarray]:
    """Swaps values between two feature channels across rows in a data copy while preserving schema."""
    validate_severity(severity)
    if severity == 0.0:
        return data.copy(deep=True) if isinstance(data, pd.DataFrame) else np.array(data, copy=True)

    faulted_data, is_df = _ensure_copy(data)
    rng = np.random.default_rng(seed)

    if is_df:
        cols = list(faulted_data.columns)
        if len(cols) < 2:
            return faulted_data
        f1, f2 = feature_pair if (feature_pair and feature_pair[0] in cols and feature_pair[1] in cols) else (cols[0], cols[1])
        mask = rng.uniform(0, 1, size=len(faulted_data)) < severity
        val1 = faulted_data.loc[mask, f1].to_numpy(copy=True)
        val2 = faulted_data.loc[mask, f2].to_numpy(copy=True)
        faulted_data.loc[mask, f1] = val2
        faulted_data.loc[mask, f2] = val1
    else:
        n_samples, n_feat = faulted_data.shape
        if n_feat < 2:
            return faulted_data
        idx1, idx2 = 0, 1
        mask = rng.uniform(0, 1, size=n_samples) < severity
        val1 = faulted_data[mask, idx1].copy()
        val2 = faulted_data[mask, idx2].copy()
        faulted_data[mask, idx1] = val2
        faulted_data[mask, idx2] = val1

    return faulted_data


def inject_sign_inversion(
    data: Union[pd.DataFrame, np.ndarray],
    severity: float,
    feature_names: Optional[List[str]] = None,
    seed: int = 42,
) -> Union[pd.DataFrame, np.ndarray]:
    """Inverts the sign of target feature values in a data copy."""
    validate_severity(severity)
    if severity == 0.0:
        return data.copy(deep=True) if isinstance(data, pd.DataFrame) else np.array(data, copy=True)

    faulted_data, is_df = _ensure_copy(data)
    rng = np.random.default_rng(seed)

    if is_df:
        cols = feature_names if feature_names else list(faulted_data.columns[:2])
        for col in cols:
            if col in faulted_data.columns:
                mask = rng.uniform(0, 1, size=len(faulted_data)) < severity
                faulted_data.loc[mask, col] = -faulted_data.loc[mask, col]
    else:
        n_samples, n_feat = faulted_data.shape
        target_indices = rng.choice(n_feat, size=min(2, n_feat), replace=False)
        for idx in target_indices:
            mask = rng.uniform(0, 1, size=n_samples) < severity
            faulted_data[mask, idx] = -faulted_data[mask, idx]

    return faulted_data


class FaultInjector:
    """
    Unified Engine for applying structured fault injection families to dataset copies.
    """

    inject_feature_bias = staticmethod(inject_feature_bias)
    inject_gain_error = staticmethod(inject_gain_error)
    inject_stuck_at = staticmethod(inject_stuck_at)
    inject_channel_swap = staticmethod(inject_channel_swap)
    inject_sign_inversion = staticmethod(inject_sign_inversion)

    FAULT_MAP = {
        FaultType.SENSOR_BIAS: inject_feature_bias,
        "Sensor_Bias": inject_feature_bias,
        "Feature_Bias": inject_feature_bias,
        FaultType.GAIN_ERROR: inject_gain_error,
        "Gain_Error": inject_gain_error,
        FaultType.STUCK_AT: inject_stuck_at,
        "Stuck_At": inject_stuck_at,
        FaultType.CHANNEL_SWAP: inject_channel_swap,
        "Channel_Swap": inject_channel_swap,
        FaultType.SIGN_INVERSION: inject_sign_inversion,
        "Sign_Inversion": inject_sign_inversion,
    }

    @classmethod
    def inject(
        cls,
        data: Union[pd.DataFrame, np.ndarray],
        fault_type: Union[FaultType, str],
        severity: float,
        feature_names: Optional[List[str]] = None,
        seed: int = 42,
        **kwargs,
    ) -> Tuple[Union[pd.DataFrame, np.ndarray], FaultInjectionResult]:
        """
        Injects a specified fault family into a copy of data without modifying source.
        """
        fault_key = str(fault_type)
        if fault_key not in cls.FAULT_MAP:
            raise DatasetValidationError(
                f"Unsupported fault_type '{fault_type}'. Supported types: {list(cls.FAULT_MAP.keys())}."
            )

        func = cls.FAULT_MAP[fault_key]
        orig_shape = (len(data), len(data.columns)) if isinstance(data, pd.DataFrame) else data.shape

        faulted_data = func(data, severity=severity, seed=seed, **kwargs)
        trans_shape = (len(faulted_data), len(faulted_data.columns)) if isinstance(faulted_data, pd.DataFrame) else faulted_data.shape

        affected = feature_names if feature_names else (
            list(data.columns[:2]) if isinstance(data, pd.DataFrame) else [f"feature_{i}" for i in range(min(2, orig_shape[1]))]
        )

        res = FaultInjectionResult(
            status=ReliabilityStatus.AVAILABLE,
            fault_type=fault_key,
            severity=severity,
            affected_features=affected,
            transformation_metadata={"seed": seed, "kwargs": kwargs},
            random_state=seed,
            original_shape=orig_shape,
            transformed_shape=trans_shape,
            warnings=[],
            limitations=[
                "Fault injection simulates controlled experimental corruptions.",
                "Injected faults are synthetic test perturbations, not proven causal hardware failures.",
            ],
        )

        return faulted_data, res

