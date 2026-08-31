"""
AEGIS-X Failure Signatures Module.

Provides condition-profile aggregation logic for Module 8R failure memory.
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from aegis.core.contracts import FailureEvent
from aegis.core.exceptions import DatasetValidationError


class ConditionProfileExtractor:
    """
    Aggregates observation-level failure events or evaluation runs into condition profiles
    for unsupervised failure signature discovery (Module 8R).
    """

    SIGNATURE_FEATURES = [
        "mean_ood_risk",
        "mean_uncertainty",
        "mean_drift_score",
        "mean_fused_risk",
        "failure_rate",
        "silent_failure_rate",
    ]

    @classmethod
    def extract_profiles_from_events(
        cls,
        events: List[FailureEvent],
        group_by_key: str = "fault_type",
    ) -> pd.DataFrame:
        """
        Groups failure events by condition (e.g. fault_type or stress run) and extracts
        aggregated numerical condition profiles.
        
        NOTE: Fault labels are used ONLY for grouping condition profiles, NOT as clustering inputs.
        """
        if not events:
            raise DatasetValidationError("Cannot extract condition profiles from empty events list.")

        records = []
        for ev in events:
            rec = {
                "sample_id": ev.sample_id,
                "group_key": str(getattr(ev, group_by_key, ev.metadata.get(group_by_key, "unknown"))),
                "ood_risk": ev.ood_risk,
                "uncertainty_risk": ev.uncertainty_risk,
                "drift_risk": ev.drift_risk,
                "fused_risk": ev.fused_risk,
                "has_actual_failure": 1.0 if ev.has_actual_failure is True else 0.0,
                "is_silent_failure": 1.0 if ev.is_silent_failure is True else 0.0,
            }
            records.append(rec)

        df_events = pd.DataFrame(records)
        profile_rows = []

        for g_key, group in df_events.groupby("group_key"):
            mean_ood = float(group["ood_risk"].mean())
            mean_unc = float(group["uncertainty_risk"].mean())
            mean_drift = float(group["drift_risk"].mean())
            mean_fused = float(group["fused_risk"].mean())
            fail_rate = float(group["has_actual_failure"].mean())
            silent_rate = float(group["is_silent_failure"].mean())

            profile_rows.append({
                "group_key": g_key,
                "mean_ood_risk": mean_ood,
                "mean_uncertainty": mean_unc,
                "mean_drift_score": mean_drift,
                "mean_fused_risk": mean_fused,
                "failure_rate": fail_rate,
                "silent_failure_rate": silent_rate,
            })

        return pd.DataFrame(profile_rows)
