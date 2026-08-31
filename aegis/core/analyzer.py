"""
AEGIS-X Core Reliability Analyzer Module.

Coordinates OOD, Uncertainty, and Drift detection engines without fusion.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from aegis.core.contracts import (
    CoreReliabilityResult,
    DriftResult,
    OODResult,
    ReliabilityStatus,
    UncertaintyResult,
)
from aegis.core.exceptions import DatasetValidationError
from aegis.core.reference_state import ReferenceState
from aegis.drift.detector import DriftDetector
from aegis.ood.detector import OODDetector
from aegis.uncertainty.estimator import UncertaintyEstimator


class CoreReliabilityAnalyzer:
    """
    Lightweight coordinator for OOD, Uncertainty, and Drift reliability detection engines.
    """

    def __init__(
        self,
        ood_method: str = "mahalanobis",
        uncertainty_method: str = "predictive_entropy",
        drift_method: str = "ks_test",
        random_state: int = 42,
    ) -> None:
        self.ood_detector: OODDetector = OODDetector(method=ood_method, random_state=random_state)
        self.uncertainty_estimator: UncertaintyEstimator = UncertaintyEstimator(method=uncertainty_method)
        self.drift_detector: DriftDetector = DriftDetector(method=drift_method)
        self.reference_state: Optional[ReferenceState] = None
        self.is_fitted: bool = False

    def fit_reference(
        self,
        reference_data: Union[pd.DataFrame, np.ndarray],
        feature_names: Optional[List[str]] = None,
        calibration_data: Optional[Union[pd.DataFrame, np.ndarray]] = None,
        calibration_labels: Optional[Union[pd.Series, np.ndarray, list]] = None,
        model_adapter: Optional[Any] = None,
    ) -> "CoreReliabilityAnalyzer":
        """Fits reference state across OOD, Drift, and optional Platt calibrator."""
        self.reference_state = ReferenceState(feature_names=feature_names)
        self.reference_state.fit(reference_data)

        self.ood_detector.fit(self.reference_state)
        self.drift_detector.fit(self.reference_state)

        # Optional calibration setup if calibration dataset provided
        if calibration_data is not None and calibration_labels is not None and model_adapter is not None:
            has_prob = getattr(
                model_adapter, "supports_predict_proba", getattr(model_adapter, "probability_supported", False)
            )
            if has_prob:
                raw_probs = model_adapter.predict_proba(calibration_data)
                self.uncertainty_estimator.fit_calibrator(raw_probs, calibration_labels)

        self.is_fitted = True
        return self

    def analyze(
        self,
        evaluation_data: Union[pd.DataFrame, np.ndarray],
        model_adapter: Optional[Any] = None,
    ) -> CoreReliabilityResult:
        """Executes OOD, Uncertainty, and Drift analyses on evaluation data without fusion."""
        if not self.is_fitted:
            raise DatasetValidationError("CoreReliabilityAnalyzer must be fitted before calling analyze().")

        ood_res: OODResult = self.ood_detector.analyze(evaluation_data)
        unc_res: UncertaintyResult = self.uncertainty_estimator.analyze(evaluation_data, model_adapter=model_adapter)
        drift_res: DriftResult = self.drift_detector.analyze(evaluation_data)

        overall_warnings: List[str] = []
        overall_warnings.extend(ood_res.warnings)
        overall_warnings.extend(unc_res.warnings)
        overall_warnings.extend(drift_res.warnings)

        capability_summary: Dict[str, Any] = {
            "ood_status": ood_res.status,
            "uncertainty_status": unc_res.status,
            "drift_status": drift_res.status,
            "is_calibrated": unc_res.is_calibrated,
            "aggregate_ood_risk": ood_res.aggregate_risk,
            "aggregate_uncertainty": unc_res.aggregate_uncertainty,
            "aggregate_drift_score": drift_res.aggregate_drift_score,
            "drift_detected": drift_res.drift_detected,
        }

        return CoreReliabilityResult(
            ood=ood_res,
            uncertainty=unc_res,
            drift=drift_res,
            warnings=overall_warnings,
            capability_summary=capability_summary,
        )

    def analyze_with_fusion(
        self,
        evaluation_data: Union[pd.DataFrame, np.ndarray],
        fusion_engine: Any,
        model_adapter: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Executes core detection layer and fuses reliability signals while preserving access to raw signals."""
        core_res = self.analyze(evaluation_data, model_adapter=model_adapter)
        fusion_res = fusion_engine.fuse(core_res.ood, core_res.uncertainty, core_res.drift)

        return {
            "core_results": core_res,
            "fusion": fusion_res,
            "aggregate_fused_risk": fusion_res.aggregate_fused_risk,
        }
