"""
Unit tests for Early Warning Horizon representation and lead calculation.
"""

import numpy as np
import pandas as pd
import pytest

from aegis.core.contracts import WarningHorizon
from aegis.warning.horizon import EarlyWarningHorizonEvaluator


def test_warning_horizon_unit():
    horizon = WarningHorizon(value=3, unit="controlled_degradation_states")
    assert horizon.value == 3
    assert horizon.unit == "controlled_degradation_states"
    # Must NOT default to clock time
    assert horizon.unit != "seconds"
    assert horizon.unit != "minutes"


def test_trajectory_lead_calculation():
    # Trajectory 0: Fails at index 3. First warning at index 1. Lead = 3 - 1 = 2 steps.
    df = pd.DataFrame({
        "trajectory_id": [0, 0, 0, 0, 0],
        "Failure_Rate": [0.0, 0.0, 0.0, 0.15, 0.20],
        "warning_probability": [0.1, 0.6, 0.8, 0.9, 0.95],
    })

    metrics, results = EarlyWarningHorizonEvaluator.evaluate_trajectories(
        df, horizon_val=3, threshold=0.5, failure_boundary=0.10
    )

    assert metrics["early_warning_coverage"] == 1.0
    assert metrics["mean_lead_steps"] == 2.0
    assert len(results) == 1
    assert results[0].lead_steps == 2
    assert results[0].is_early_warning is True
