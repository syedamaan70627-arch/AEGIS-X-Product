"""
Unit tests for AEGIS-X Condition Profile Extractor and Failure Signatures.
"""

import pandas as pd
import pytest

from aegis.core.contracts import FailureEvent
from aegis.failure_memory.signatures import ConditionProfileExtractor


def test_condition_profile_extractor():
    events = [
        FailureEvent(
            sample_id=i,
            ood_risk=0.1 * i,
            uncertainty_risk=0.2 * i,
            drift_risk=0.05,
            fused_risk=0.15 * i,
            is_high_risk_warning=(i > 2),
            fault_type="Sensor_Bias" if i < 3 else "Gain_Error",
            has_actual_failure=(i > 3),
            is_silent_failure=(i == 3),
        )
        for i in range(6)
    ]

    profiles = ConditionProfileExtractor.extract_profiles_from_events(events, group_by_key="fault_type")

    assert len(profiles) == 2  # 2 groups: Sensor_Bias and Gain_Error
    assert set(ConditionProfileExtractor.SIGNATURE_FEATURES).issubset(set(profiles.columns))
    # Group key column exists for post-hoc grouping
    assert "group_key" in profiles.columns
