"""
AEGIS-X Controlled Stress Engine Module.

Provides explicit controlled stress testing workflows while preserving scientific negative findings.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score

from aegis.core.contracts import ReliabilityStatus, StressTestResult
from aegis.core.exceptions import DatasetValidationError
from aegis.stress.corruptions import (
    combined_stress,
    feature_dropout_stress,
    feature_permutation_stress,
    gaussian_noise_stress,
    validate_severity,
)


class ControlledStressEngine:
    """
    Explicit controlled stress testing lab for evaluating model and fusion degradation
    under synthetic feature noise, dropout, and permutation.
    """

    STRESS_GENERATORS = {
        "Gaussian_Noise": gaussian_noise_stress,
        "Feature_Dropout": feature_dropout_stress,
        "Feature_Permutation": feature_permutation_stress,
        "Combined_Stress": combined_stress,
    }

    def __init__(self, random_state: int = 42) -> None:
        self.random_state: int = random_state

    def run_stress_test(
        self,
        evaluation_data: Union[pd.DataFrame, np.ndarray],
        stress_type: str = "Gaussian_Noise",
        severity: float = 0.2,
        model_adapter: Optional[Any] = None,
        core_analyzer: Optional[Any] = None,
        fusion_engine: Optional[Any] = None,
        y_true: Optional[Union[pd.Series, np.ndarray, list]] = None,
        random_state: Optional[int] = None,
    ) -> StressTestResult:
        """
        Executes controlled stress corruption on a copy of evaluation data.
        Never mutates incoming evaluation_data.
        """
        validate_severity(severity)

        if stress_type not in self.STRESS_GENERATORS:
            raise DatasetValidationError(
                f"Unsupported stress_type '{stress_type}'. Supported types: {list(self.STRESS_GENERATORS.keys())}."
            )

        seed = random_state if random_state is not None else self.random_state
        generator = self.STRESS_GENERATORS[stress_type]

        try:
            # Generate stressed copy without mutating source
            stressed_data = generator(evaluation_data, severity=severity, seed=seed)

            # Evaluate original baseline signals if analyzer provided
            orig_risk = 0.0
            stressed_risk = 0.0
            warnings_list: List[str] = []

            if core_analyzer is not None and core_analyzer.is_fitted:
                orig_res = core_analyzer.analyze(evaluation_data, model_adapter=model_adapter)
                stressed_res = core_analyzer.analyze(stressed_data, model_adapter=model_adapter)

                if fusion_engine is not None:
                    orig_fusion = fusion_engine.fuse(orig_res.ood, orig_res.uncertainty, orig_res.drift)
                    stressed_fusion = fusion_engine.fuse(stressed_res.ood, stressed_res.uncertainty, stressed_res.drift)
                    orig_risk = orig_fusion.aggregate_fused_risk
                    stressed_risk = stressed_fusion.aggregate_fused_risk
                else:
                    orig_risk = orig_res.capability_summary.get("aggregate_ood_risk", 0.0)
                    stressed_risk = stressed_res.capability_summary.get("aggregate_ood_risk", 0.0)

            risk_delta = float(stressed_risk - orig_risk)

            # Optional Label-Aware Diagnostics
            orig_acc: Optional[float] = None
            stressed_acc: Optional[float] = None
            acc_delta: Optional[float] = None

            if y_true is not None and model_adapter is not None:
                y_arr = np.asarray(y_true)
                orig_preds = model_adapter.predict(evaluation_data)
                stressed_preds = model_adapter.predict(stressed_data)

                orig_acc = float(accuracy_score(y_arr, orig_preds))
                stressed_acc = float(accuracy_score(y_arr, stressed_preds))
                acc_delta = float(stressed_acc - orig_acc)

                # Check for Module 6 negative result condition (accuracy drops while risk fails to rise proportionally)
                if acc_delta < -0.15 and risk_delta < 0.05:
                    warnings_list.append(
                        "Negative Stress Result Detected (Module 6 Failure Mode): Accuracy degraded significantly without corresponding fusion risk escalation."
                    )

            return StressTestResult(
                status=ReliabilityStatus.AVAILABLE,
                stress_type=stress_type,
                severity=severity,
                original_risk=orig_risk,
                stressed_risk=stressed_risk,
                risk_delta=risk_delta,
                accuracy_delta=acc_delta,
                original_accuracy=orig_acc,
                stressed_accuracy=stressed_acc,
                details={
                    "seed": seed,
                    "num_samples": len(evaluation_data),
                    "is_label_aware": y_true is not None,
                    "fusion_method": getattr(fusion_engine, "__class__", {}).__name__ if fusion_engine else None,
                },
                warnings=warnings_list,
                limitations=[
                    "Controlled stress testing simulates synthetic noise/dropout/permutation.",
                    "Label-free stress analysis measures risk delta; label-aware analysis measures accuracy delta.",
                ],
            )
        except Exception as e:
            return StressTestResult(
                status=ReliabilityStatus.ERROR,
                stress_type=stress_type,
                severity=severity,
                original_risk=0.0,
                stressed_risk=0.0,
                risk_delta=0.0,
                warnings=[f"Controlled stress test execution failed: {str(e)}"],
            )
