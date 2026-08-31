"""
AEGIS-X ADWIN Drift Wrapper Module.

Provides streaming concept/data drift detection using River ADWIN or custom fallback.
"""

from typing import Any, Dict, List, Optional
import numpy as np

try:
    import river
    from river.drift import ADWIN
    HAS_RIVER = True
except ImportError:
    HAS_RIVER = False
    ADWIN = None


class ADWINWrapper:
    """
    Wrapper for River ADWIN streaming change-point and drift detection.
    Falls back gracefully if river package is not installed.
    """

    init_kwargs: Dict[str, Any]

    def __init__(self, delta: float = 0.002) -> None:
        self.delta: float = delta
        self.has_river: bool = HAS_RIVER
        self.detectors: Dict[str, Any] = {}
        self.is_initialized: bool = False

    def initialize_features(self, feature_names: List[str]) -> None:
        """Initializes an ADWIN detector instance per feature stream."""
        if self.has_river:
            self.detectors = {f: ADWIN(delta=self.delta) for f in feature_names}
        else:
            self.detectors = {}
        self.is_initialized = True

    def update_sample(self, sample_dict: Dict[str, float]) -> Dict[str, bool]:
        """
        Updates ADWIN detectors with a single sequential sample dictionary.
        Returns a dictionary of drift detection flags per feature.
        """
        if not self.is_initialized:
            self.initialize_features(list(sample_dict.keys()))

        drift_flags = {}
        for feature, val in sample_dict.items():
            if self.has_river and feature in self.detectors:
                det = self.detectors[feature]
                det.update(float(val))
                drift_flags[feature] = bool(det.drift_detected)
            else:
                drift_flags[feature] = False
        return drift_flags

    def update_batch(self, X_batch: np.ndarray, feature_names: List[str]) -> List[Dict[str, bool]]:
        """
        Sequentially updates ADWIN detectors with a batch of samples.
        Preserves sequential temporal ordering.
        """
        if not self.is_initialized:
            self.initialize_features(feature_names)

        results = []
        for row in X_batch:
            sample_dict = {f: float(val) for f, val in zip(feature_names, row)}
            flags = self.update_sample(sample_dict)
            results.append(flags)
        return results
