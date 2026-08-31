"""
AEGIS-X Early Warning Feature Builder Module.

Constructs Dynamic Multi-Signal feature vectors for Module 10 temporal early warning
while enforcing strict backward-looking temporal safety.
"""

from typing import List, Tuple
import numpy as np
import pandas as pd

from aegis.core.exceptions import DatasetValidationError


class EarlyWarningFeatureBuilder:
    """
    Constructs Dynamic Multi-Signal features for temporal early warning engines.
    """

    DYNAMIC_MULTI_SIGNAL_FEATURES = [
        "ood_risk",
        "uncertainty_risk",
        "drift_risk",
        "fused_risk",
        "delta_ood_risk",
        "delta_uncertainty_risk",
        "delta_drift_risk",
        "delta_fused_risk",
    ]

    @classmethod
    def build_features(cls, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Builds Dynamic Multi-Signal feature vector with backward-looking deltas.
        Never mutates incoming DataFrame.
        """
        data_copy = df.copy(deep=True)

        for base_feat in ["ood_risk", "uncertainty_risk", "drift_risk", "fused_risk"]:
            delta_col = f"delta_{base_feat}"
            if base_feat in data_copy.columns and delta_col not in data_copy.columns:
                data_copy[delta_col] = data_copy[base_feat].diff().fillna(0.0)

        missing = [f for f in cls.DYNAMIC_MULTI_SIGNAL_FEATURES if f not in data_copy.columns]
        if missing:
            raise DatasetValidationError(f"DataFrame missing required Early Warning features: {missing}")

        return data_copy[cls.DYNAMIC_MULTI_SIGNAL_FEATURES].copy(), cls.DYNAMIC_MULTI_SIGNAL_FEATURES
