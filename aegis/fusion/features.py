"""
AEGIS-X Fusion Feature Transformer Module.

Constructs 7-dimensional interaction feature vectors from core reliability signals:
[S_ood, U, D, S_ood * U, S_ood * D, U * D, S_ood * U * D]
"""

from typing import Union
import numpy as np
import pandas as pd


class FusionFeatureTransformer:
    """
    Transforms individual reliability signals (OOD, Uncertainty, Drift) into
    the 7-dimensional interaction feature matrix validated in research Modules 5 and 6R.
    """

    @staticmethod
    def transform_signals(
        ood_signal: Union[np.ndarray, list, float],
        uncertainty_signal: Union[np.ndarray, list, float],
        drift_signal: Union[np.ndarray, list, float],
    ) -> np.ndarray:
        """
        Constructs interaction feature array.
        
        :param ood_signal: Normalized OOD risk array or scalar in [0, 1].
        :param uncertainty_signal: Normalized uncertainty array or scalar in [0, 1].
        :param drift_signal: Normalized drift score array or scalar in [0, 1].
        :return: 2D numpy array of shape (N, 7) with interaction terms.
        """
        s_ood = np.atleast_1d(np.asarray(ood_signal, dtype=np.float64))
        u = np.atleast_1d(np.asarray(uncertainty_signal, dtype=np.float64))
        d = np.atleast_1d(np.asarray(drift_signal, dtype=np.float64))

        # Broadcast scalar drift to match array length if needed
        max_len = max(len(s_ood), len(u), len(d))
        if len(s_ood) == 1 and max_len > 1:
            s_ood = np.full(max_len, s_ood[0])
        if len(u) == 1 and max_len > 1:
            u = np.full(max_len, u[0])
        if len(d) == 1 and max_len > 1:
            d = np.full(max_len, d[0])

        if not (len(s_ood) == len(u) == len(d)):
            raise ValueError(
                f"Signal array lengths mismatch: OOD ({len(s_ood)}), Uncertainty ({len(u)}), Drift ({len(d)})."
            )

        # Base terms
        f1 = s_ood
        f2 = u
        f3 = d

        # Pairwise interaction terms
        f4 = s_ood * u
        f5 = s_ood * d
        f6 = u * d

        # Three-way interaction term
        f7 = s_ood * u * d

        return np.column_stack([f1, f2, f3, f4, f5, f6, f7])
