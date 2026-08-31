"""
AEGIS-X Failure Prediction Feature Builder Module.

Constructs static, dynamic (backward-looking deltas), and signature-aware feature matrices
for Module 9R onset-aware failure prediction while guaranteeing strict temporal safety.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from aegis.core.exceptions import DatasetValidationError


class PredictionFeatureBuilder:
    """
    Constructs feature matrices for failure prediction while enforcing temporal safety
    (no future state leakage) and excluding controlled severity as a predictor.
    """

    STATIC_FEATURES = [
        "ood_risk",
        "uncertainty_risk",
        "drift_risk",
        "fused_risk",
    ]

    DYNAMIC_FEATURES = [
        "ood_risk",
        "uncertainty_risk",
        "drift_risk",
        "fused_risk",
        "delta_ood_risk",
        "delta_uncertainty_risk",
        "delta_drift_risk",
        "delta_fused_risk",
    ]

    SIGNATURE_FEATURES = [
        "ood_risk",
        "uncertainty_risk",
        "drift_risk",
        "fused_risk",
        "delta_ood_risk",
        "delta_uncertainty_risk",
        "delta_drift_risk",
        "delta_fused_risk",
        "signature_distance",
        "is_known_pattern",
    ]

    FEATURE_SETS = {
        "static": STATIC_FEATURES,
        "dynamic": DYNAMIC_FEATURES,
        "signature": SIGNATURE_FEATURES,
    }

    @classmethod
    def build_features(
        cls,
        df: pd.DataFrame,
        feature_set_type: str = "dynamic",
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Constructs prediction feature matrix with backward-looking deltas.
        Operates strictly on a copy without mutating incoming DataFrame.
        """
        if feature_set_type not in cls.FEATURE_SETS:
            raise DatasetValidationError(
                f"Unsupported feature_set_type '{feature_set_type}'. Supported: {list(cls.FEATURE_SETS.keys())}."
            )

        data_copy = df.copy(deep=True)

        # Compute backward-looking deltas (f_t - f_{t-1}) if dynamic or signature mode
        for base_feat in ["ood_risk", "uncertainty_risk", "drift_risk", "fused_risk"]:
            delta_col = f"delta_{base_feat}"
            if base_feat in data_copy.columns and delta_col not in data_copy.columns:
                # Backward-looking diff along trajectory (filling initial diff with 0.0)
                data_copy[delta_col] = data_copy[base_feat].diff().fillna(0.0)

        # Default fallback for missing optional columns
        for col in ["signature_distance", "is_known_pattern"]:
            if col not in data_copy.columns:
                data_copy[col] = 0.0 if col == "signature_distance" else 1.0

        target_features = cls.FEATURE_SETS[feature_set_type]

        # Verify all target features are present
        missing = [f for f in target_features if f not in data_copy.columns]
        if missing:
            raise DatasetValidationError(f"DataFrame missing required prediction features: {missing}")

        return data_copy[target_features].copy(), target_features
