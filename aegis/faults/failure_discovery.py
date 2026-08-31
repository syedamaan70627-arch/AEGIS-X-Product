"""
AEGIS-X Failure Discovery Engine Module.

Provides label-free and label-aware failure discovery, silent failure identification,
and fault-family reliability diagnostic reports.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score

from aegis.core.contracts import (
    FailureDiscoveryResult,
    FailureEvent,
    ReliabilityStatus,
)
from aegis.core.exceptions import DatasetValidationError


class FailureDiscoveryEngine:
    """
    Failure Discovery Engine for detecting model failures, high-risk operational states,
    and silent failure conditions across structured fault injections.
    """

    def __init__(self, default_risk_threshold: float = 0.5) -> None:
        self.default_risk_threshold: float = default_risk_threshold

    def discover_failures(
        self,
        faulted_data: Union[pd.DataFrame, np.ndarray],
        original_data: Optional[Union[pd.DataFrame, np.ndarray]] = None,
        y_true: Optional[Union[pd.Series, np.ndarray, list]] = None,
        model_adapter: Optional[Any] = None,
        core_analyzer: Optional[Any] = None,
        fusion_engine: Optional[Any] = None,
        fault_type: Optional[str] = None,
        severity: Optional[float] = None,
        risk_threshold: Optional[float] = None,
    ) -> FailureDiscoveryResult:
        """
        Evaluates faulted dataset for reliability warnings, model failures, and silent failures.
        """
        threshold = risk_threshold if risk_threshold is not None else self.default_risk_threshold
        is_label_aware = y_true is not None and model_adapter is not None

        num_samples = len(faulted_data)
        if num_samples == 0:
            raise DatasetValidationError("Cannot run failure discovery on an empty dataset.")

        try:
            # 1. Run core reliability detection layer & fusion if analyzer is available
            ood_scores = np.zeros(num_samples)
            unc_scores = np.zeros(num_samples)
            drift_score = 0.0
            fused_scores = np.zeros(num_samples)

            if core_analyzer is not None and core_analyzer.is_fitted:
                core_res = core_analyzer.analyze(faulted_data, model_adapter=model_adapter)
                if core_res.ood.risk_scores is not None:
                    ood_scores = np.atleast_1d(np.asarray(core_res.ood.risk_scores))
                if core_res.uncertainty.uncertainty_scores is not None:
                    unc_scores = np.atleast_1d(np.asarray(core_res.uncertainty.uncertainty_scores))
                drift_score = float(core_res.drift.aggregate_drift_score)

                if fusion_engine is not None:
                    fusion_res = fusion_engine.fuse(core_res.ood, core_res.uncertainty, core_res.drift)
                    if fusion_res.fused_risk_scores is not None:
                        fused_scores = np.atleast_1d(np.asarray(fusion_res.fused_risk_scores))

            # 2. Evaluate predictions if model_adapter is available
            actual_preds = None
            orig_preds = None
            if model_adapter is not None:
                actual_preds = model_adapter.predict(faulted_data)
                if original_data is not None:
                    orig_preds = model_adapter.predict(original_data)

            # 3. Label-Aware Evaluation (if y_true is available)
            has_failures: Optional[np.ndarray] = None
            if is_label_aware:
                y_arr = np.asarray(y_true)
                has_failures = (actual_preds != y_arr).astype(bool)

            # 4. High-risk warning identification
            high_risk_warnings = (fused_scores >= threshold)
            total_warnings = int(np.sum(high_risk_warnings))

            total_failures: Optional[int] = None
            silent_failures: Optional[int] = None
            silent_failure_rate: Optional[float] = None

            if is_label_aware and has_failures is not None:
                total_failures = int(np.sum(has_failures))
                # Silent Failure: Actual failure occurs (1) BUT high-risk warning is NOT triggered (0)
                silent_mask = has_failures & (~high_risk_warnings)
                silent_failures = int(np.sum(silent_mask))
                silent_failure_rate = float(silent_failures / total_failures) if total_failures > 0 else 0.0

            # 5. Build individual FailureEvents
            failure_events: List[FailureEvent] = []
            for i in range(num_samples):
                actual_fail = bool(has_failures[i]) if is_label_aware and has_failures is not None else None
                is_silent = bool(actual_fail and not high_risk_warnings[i]) if is_label_aware and actual_fail is not None else None

                event = FailureEvent(
                    sample_id=i,
                    ood_risk=float(ood_scores[i]) if i < len(ood_scores) else 0.0,
                    uncertainty_risk=float(unc_scores[i]) if i < len(unc_scores) else 0.0,
                    drift_risk=drift_score,
                    fused_risk=float(fused_scores[i]) if i < len(fused_scores) else 0.0,
                    is_high_risk_warning=bool(high_risk_warnings[i]),
                    fault_type=fault_type,
                    severity=severity,
                    has_actual_failure=actual_fail,
                    is_silent_failure=is_silent,
                    metadata={
                        "prediction_changed": bool(orig_preds[i] != actual_preds[i]) if orig_preds is not None and actual_preds is not None else False
                    },
                )
                failure_events.append(event)

            # 6. Summary breakdown
            summary_by_fault = {
                "fault_type": fault_type,
                "severity": severity,
                "num_samples": num_samples,
                "total_warnings": total_warnings,
                "warning_rate": float(total_warnings / num_samples),
                "mean_fused_risk": float(np.mean(fused_scores)),
                "is_label_aware": is_label_aware,
                "total_failures": total_failures,
                "silent_failures": silent_failures,
                "silent_failure_rate": silent_failure_rate,
            }

            warnings_list: List[str] = []
            if silent_failures is not None and silent_failures > 0:
                warnings_list.append(
                    f"Confirmed Silent Failure Alert: {silent_failures} model failures occurred without triggering high-risk warning (Threshold = {threshold})."
                )

            return FailureDiscoveryResult(
                status=ReliabilityStatus.AVAILABLE,
                is_label_aware=is_label_aware,
                total_samples=num_samples,
                total_warnings=total_warnings,
                total_failures=total_failures,
                silent_failures=silent_failures,
                silent_failure_rate=silent_failure_rate,
                failure_events=failure_events,
                summary_by_fault=summary_by_fault,
                warnings=warnings_list,
                limitations=[
                    "Silent failure discovery requires ground truth evaluation labels y_true.",
                    "Label-free mode identifies high-risk warnings and prediction changes without claiming confirmed model failures.",
                ],
            )
        except Exception as e:
            return FailureDiscoveryResult(
                status=ReliabilityStatus.ERROR,
                is_label_aware=is_label_aware,
                total_samples=num_samples,
                total_warnings=0,
                warnings=[f"Failure discovery execution failed: {str(e)}"],
            )
