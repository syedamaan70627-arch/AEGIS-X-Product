"""
AEGIS-X Bootstrap Confidence Interval Module (Module 13).

Provides non-parametric bootstrap resampling for computing 95% percentile confidence intervals.
"""

from typing import Union
import numpy as np
import pandas as pd

from aegis.core.contracts import BootstrapInterval


def bootstrap_mean_ci(
    data: Union[np.ndarray, pd.Series, list],
    n_bootstrap: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> BootstrapInterval:
    """
    Computes a non-parametric bootstrap percentile confidence interval for the mean of data.
    """
    arr = np.asarray(data, dtype=np.float64)
    if len(arr) == 0:
        return BootstrapInterval(estimate=0.0, lower=0.0, upper=0.0, confidence_level=ci)

    mean_estimate = float(np.mean(arr))
    if len(arr) == 1:
        return BootstrapInterval(estimate=mean_estimate, lower=mean_estimate, upper=mean_estimate, confidence_level=ci)

    rng = np.random.default_rng(seed)
    n_samples = len(arr)

    # Resample with replacement
    bootstrap_indices = rng.integers(0, n_samples, size=(n_bootstrap, n_samples))
    bootstrap_means = np.mean(arr[bootstrap_indices], axis=1)

    alpha = (1.0 - ci) / 2.0
    lower_pct = float(np.percentile(bootstrap_means, alpha * 100.0))
    upper_pct = float(np.percentile(bootstrap_means, (1.0 - alpha) * 100.0))

    return BootstrapInterval(
        estimate=mean_estimate,
        lower=lower_pct,
        upper=upper_pct,
        confidence_level=ci,
    )
