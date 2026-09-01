"""
AEGIS-X Temporal Target & Group Split Scientific Integrity Tests.

Verifies:
1. Exact future Failure_Within_3 invariant ([0,0,0,0,0,0,1,1,1,1] -> [0,0,0,1,1,1,1,1,1,0]).
2. Future targets & onset targets never cross trajectory boundaries.
3. Group-aware 70/30 trajectory splitting asserts set(train_trajs).isdisjoint(set(val_trajs)).
4. Insufficient independent trajectories raise DatasetValidationError.
5. Duplicate (trajectory_id, step) pairs raise DatasetValidationError.
6. Unsorted uploaded temporal data is safely sorted by (trajectory_id, step).
7. Mismatching user-supplied targets are rejected with DatasetValidationError.
8. Non-binary target columns are rejected.
9. sample_temporal_trajectory.csv fixture targets match recomputed ground truth exactly.
"""

import io
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from aegis.core.exceptions import DatasetValidationError
from aegis.core.temporal import (
    compute_future_failure_within_n,
    derive_failure_onset_next,
    derive_failure_within_n,
    split_trajectories_group_safe,
    validate_and_prep_trajectory_df,
)


def test_exact_future_failure_within_3_invariant():
    """
    Test 1: Exact future Failure_Within_3 invariant:
    Input is_failure: [0, 0, 0, 0, 0, 0, 1, 1, 1, 1]
    Expected Failure_Within_3: [0, 0, 0, 1, 1, 1, 1, 1, 1, 0]
    """
    is_fail = pd.Series([0, 0, 0, 0, 0, 0, 1, 1, 1, 1])
    res = compute_future_failure_within_n(is_fail, n=3)
    expected = [0, 0, 0, 1, 1, 1, 1, 1, 1, 0]
    assert list(res) == expected, f"Expected {expected}, got {list(res)}"


def test_future_target_never_crosses_trajectory_boundaries():
    """
    Test 2: Future target max(t+1..t+N) never inspects or mixes across trajectory boundaries.
    """
    df = pd.DataFrame({
        "trajectory_id": [0, 0, 0, 1, 1, 1],
        "step": [0, 1, 2, 0, 1, 2],
        "is_failure": [0, 0, 0, 1, 1, 1],
    })
    # Trajectory 0 ends with 0s. Trajectory 1 starts with 1s.
    # At step 2 of Trajectory 0 (index 2), future states in Trajectory 0 are empty -> Failure_Within_3 MUST be 0.
    res = derive_failure_within_n(df, n=3)
    assert res.iloc[2] == 0, f"Trajectory 0 leaked into Trajectory 1: got {res.iloc[2]}"
    assert res.iloc[5] == 0, f"Trajectory 1 last step got {res.iloc[5]}"


def test_failure_onset_next_never_crosses_trajectory_boundaries():
    """
    Test 3: Failure_Onset_Next (shift(-1)) never crosses trajectory boundaries.
    """
    df = pd.DataFrame({
        "trajectory_id": [0, 0, 0, 1, 1, 1],
        "step": [0, 1, 2, 0, 1, 2],
        "is_failure": [0, 0, 0, 1, 1, 1],
    })
    res = derive_failure_onset_next(df)
    # Index 2 is last step of Trajectory 0 -> next step in Trajectory 0 does not exist -> 0.
    assert res.iloc[2] == 0, f"Onset target crossed trajectory boundary: got {res.iloc[2]}"


def test_group_safe_trajectory_split_disjoint():
    """
    Test 4 & 5: Train and validation trajectory ID sets are disjoint. No trajectory is split across train/val.
    """
    rows = []
    for t_id in range(10):
        for s in range(5):
            rows.append({
                "trajectory_id": t_id,
                "step": s,
                "ood_risk": 0.1,
                "uncertainty_risk": 0.1,
                "drift_risk": 0.1,
                "fused_risk": 0.1,
                "is_failure": 1 if (s >= 3 and t_id >= 5) else 0,
                "Failure_Onset_Next": 0,
            })
    df = pd.DataFrame(rows)
    df["Failure_Onset_Next"] = derive_failure_onset_next(df)

    train_df, val_df = split_trajectories_group_safe(df, target_col="Failure_Onset_Next", train_ratio=0.70)

    train_trajs = set(train_df["trajectory_id"])
    val_trajs = set(val_df["trajectory_id"])

    assert train_trajs.isdisjoint(val_trajs), "Train and val trajectory IDs must be disjoint."
    assert len(train_trajs.intersection(val_trajs)) == 0


def test_insufficient_independent_trajectories_rejected():
    """
    Test 6: Single trajectory cannot be split into group-disjoint train and validation subsets.
    """
    df = pd.DataFrame({
        "trajectory_id": [0] * 10,
        "step": list(range(10)),
        "ood_risk": [0.1] * 10,
        "uncertainty_risk": [0.1] * 10,
        "drift_risk": [0.1] * 10,
        "fused_risk": [0.1] * 10,
        "is_failure": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
    })
    df["Failure_Onset_Next"] = derive_failure_onset_next(df)

    with pytest.raises(DatasetValidationError) as excinfo:
        split_trajectories_group_safe(df, target_col="Failure_Onset_Next")
    assert "Insufficient independent trajectories" in str(excinfo.value)


def test_duplicate_trajectory_id_and_step_rejected():
    """
    Test 7: Duplicate (trajectory_id, step) pairs raise DatasetValidationError.
    """
    df = pd.DataFrame({
        "trajectory_id": [0, 0, 0],
        "step": [0, 1, 1],  # Duplicate step 1
        "ood_risk": [0.1, 0.2, 0.3],
        "uncertainty_risk": [0.1, 0.2, 0.3],
        "drift_risk": [0.1, 0.2, 0.3],
        "fused_risk": [0.1, 0.2, 0.3],
        "is_failure": [0, 0, 1],
    })

    with pytest.raises(DatasetValidationError) as excinfo:
        validate_and_prep_trajectory_df(df, target_col="Failure_Onset_Next")
    assert "duplicate" in str(excinfo.value).lower()


def test_unsorted_uploaded_data_safely_sorted():
    """
    Test 8: Unsorted CSV row order is sorted by (trajectory_id, step) before processing.
    """
    df = pd.DataFrame({
        "trajectory_id": [0, 0, 0],
        "step": [2, 0, 1],  # Unsorted
        "ood_risk": [0.3, 0.1, 0.2],
        "uncertainty_risk": [0.3, 0.1, 0.2],
        "drift_risk": [0.3, 0.1, 0.2],
        "fused_risk": [0.3, 0.1, 0.2],
        "is_failure": [1, 0, 0],
    })

    clean_df = validate_and_prep_trajectory_df(df, target_col="Failure_Onset_Next")
    assert list(clean_df["step"]) == [0, 1, 2]


def test_inconsistent_supplied_failure_within_n_rejected():
    """
    Test 9: User-supplied Failure_Within_N that disagrees with is_failure ground truth is rejected.
    """
    df = pd.DataFrame({
        "trajectory_id": [0] * 10,
        "step": list(range(10)),
        "ood_risk": [0.1] * 10,
        "uncertainty_risk": [0.1] * 10,
        "drift_risk": [0.1] * 10,
        "fused_risk": [0.1] * 10,
        "is_failure": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
        "Failure_Within_3": [1] * 10,  # Wrong supplied target! (Indices 0..2 should be 0)
    })

    with pytest.raises(DatasetValidationError) as excinfo:
        validate_and_prep_trajectory_df(df, target_col="Failure_Within_3", horizon_val=3)
    assert "mismatches" in str(excinfo.value).lower() or "disagrees" in str(excinfo.value).lower()


def test_inconsistent_supplied_failure_onset_next_rejected():
    """
    Test 10: User-supplied Failure_Onset_Next that disagrees with is_failure ground truth is rejected.
    """
    df = pd.DataFrame({
        "trajectory_id": [0] * 5,
        "step": list(range(5)),
        "ood_risk": [0.1] * 5,
        "uncertainty_risk": [0.1] * 5,
        "drift_risk": [0.1] * 5,
        "fused_risk": [0.1] * 5,
        "is_failure": [0, 0, 1, 1, 1],
        "Failure_Onset_Next": [0, 0, 0, 0, 0],  # Wrong! Index 1 should be 1
    })

    with pytest.raises(DatasetValidationError) as excinfo:
        validate_and_prep_trajectory_df(df, target_col="Failure_Onset_Next")
    assert "mismatches" in str(excinfo.value).lower() or "disagrees" in str(excinfo.value).lower()


def test_non_binary_targets_rejected():
    """
    Test 11: Non-binary target values raise DatasetValidationError.
    """
    df = pd.DataFrame({
        "trajectory_id": [0, 0, 0],
        "step": [0, 1, 2],
        "ood_risk": [0.1, 0.2, 0.3],
        "uncertainty_risk": [0.1, 0.2, 0.3],
        "drift_risk": [0.1, 0.2, 0.3],
        "fused_risk": [0.1, 0.2, 0.3],
        "is_failure": [0, 2, 5],  # Invalid non-binary state
    })

    with pytest.raises(DatasetValidationError) as excinfo:
        validate_and_prep_trajectory_df(df, target_col="Failure_Onset_Next")
    assert "binary" in str(excinfo.value).lower()


def test_sample_temporal_trajectory_fixture_integrity():
    """
    Test 12: Recomputation of targets on sample_temporal_trajectory.csv matches stored CSV columns exactly.
    """
    fixture_path = Path(__file__).parents[1] / "examples" / "sample_temporal_trajectory.csv"
    assert fixture_path.exists(), "sample_temporal_trajectory.csv fixture missing!"

    df_csv = pd.read_csv(fixture_path)
    clean_df = validate_and_prep_trajectory_df(df_csv, target_col="Failure_Onset_Next")

    expected_onset = derive_failure_onset_next(clean_df)
    expected_within_3 = derive_failure_within_n(clean_df, n=3)

    assert list(df_csv["Failure_Onset_Next"]) == list(expected_onset)
    assert list(df_csv["Failure_Within_3"]) == list(expected_within_3)
