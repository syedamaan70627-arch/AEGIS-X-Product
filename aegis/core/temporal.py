"""
AEGIS-X Centralized Temporal Trajectory Processing Module.

Provides robust, scientifically verified utilities for:
1. Validating and sorting temporal trajectory datasets by trajectory_id and step.
2. Deriving next-step failure onset targets (Failure_Onset_Next) with zero cross-trajectory leakage.
3. Deriving forward-looking future horizon failure targets (Failure_Within_N).
4. Cross-validating user-supplied target columns against ground-truth is_failure sequences.
5. Performing group-aware trajectory splits (70/30) ensuring zero trajectory-level leakage.
"""

from typing import Tuple, Set, Optional
import numpy as np
import pandas as pd

from aegis.core.exceptions import DatasetValidationError


def compute_future_failure_within_n(is_failure_series: pd.Series, n: int) -> pd.Series:
    """
    Computes Failure_Within_N for a single trajectory's is_failure series.
    Failure_Within_N[t] = max(is_failure[t+1], ..., is_failure[t+N])

    - Never includes current state t.
    - Never inspects another trajectory.
    - At final states where fewer than N future states exist, uses remaining future states.
    - If no future states exist (last state of trajectory), target is 0.
    """
    vals = is_failure_series.to_numpy()
    length = len(vals)
    result = np.zeros(length, dtype=int)
    for i in range(length):
        future = vals[i + 1 : min(i + 1 + n, length)]
        if len(future) > 0:
            result[i] = int(np.max(future))
    return pd.Series(result, index=is_failure_series.index)


def derive_failure_within_n(df: pd.DataFrame, n: int) -> pd.Series:
    """
    Derives Failure_Within_N target across a dataframe grouped by trajectory_id.
    """
    if "is_failure" not in df.columns:
        raise DatasetValidationError("Dataset missing required 'is_failure' state column for target derivation.")

    if "trajectory_id" in df.columns:
        return df.groupby("trajectory_id", group_keys=False)["is_failure"].apply(
            lambda s: compute_future_failure_within_n(s, n)
        ).astype(int)
    else:
        return compute_future_failure_within_n(df["is_failure"], n).astype(int)


def derive_failure_onset_next(df: pd.DataFrame) -> pd.Series:
    """
    Derives Failure_Onset_Next target across a dataframe grouped by trajectory_id.
    Failure_Onset_Next[t] = is_failure[t+1]
    """
    if "is_failure" not in df.columns:
        raise DatasetValidationError("Dataset missing required 'is_failure' state column for target derivation.")

    if "trajectory_id" in df.columns:
        return (
            df.groupby("trajectory_id", group_keys=False)["is_failure"]
            .shift(-1)
            .fillna(0)
            .astype(int)
        )
    else:
        return df["is_failure"].shift(-1).fillna(0).astype(int)


def validate_and_prep_trajectory_df(
    df: pd.DataFrame,
    target_col: str,
    horizon_val: Optional[int] = None,
) -> pd.DataFrame:
    """
    Validates schema, temporal ordering (trajectory_id, step), duplicate pairs, and target consistency.
    Returns cleaned, sorted DataFrame with verified target_col.
    """
    df = df.copy()

    # 1. Require trajectory_id and step
    if "trajectory_id" not in df.columns:
        raise DatasetValidationError("Temporal trajectory dataset must contain a 'trajectory_id' column.")

    if "step" not in df.columns and "sequence_step" in df.columns:
        df["step"] = df["sequence_step"]

    if "step" not in df.columns:
        raise DatasetValidationError("Temporal trajectory dataset must contain a 'step' column.")

    # 2. Check for duplicate (trajectory_id, step) pairs
    duplicates = df.duplicated(subset=["trajectory_id", "step"])
    if duplicates.any():
        dup_count = duplicates.sum()
        raise DatasetValidationError(f"Found {dup_count} duplicate (trajectory_id, step) pairs in dataset.")

    # 3. Sort deterministically by trajectory_id and step
    df = df.sort_values(by=["trajectory_id", "step"]).reset_index(drop=True)

    # 4. Check required signal columns
    required_signals = {"ood_risk", "uncertainty_risk", "drift_risk", "fused_risk"}
    missing_signals = required_signals - set(df.columns)
    if missing_signals:
        raise DatasetValidationError(
            f"Raw feature dataset cannot be used for temporal setup. "
            f"Dataset must contain temporal reliability signals: {sorted(list(missing_signals))}."
        )

    # 5. Handle Target Derivation & Consistency Cross-Validation
    if "is_failure" in df.columns:
        # Validate is_failure is binary
        if not set(df["is_failure"].unique()).issubset({0, 1, 0.0, 1.0}):
            raise DatasetValidationError("'is_failure' column must contain binary values (0 or 1).")
        df["is_failure"] = df["is_failure"].astype(int)

        # Derive expected target based on target_col name or horizon_val
        if target_col == "Failure_Onset_Next":
            expected_target = derive_failure_onset_next(df)
        elif target_col.startswith("Failure_Within_") or horizon_val is not None:
            n = horizon_val if horizon_val is not None else int(target_col.split("_")[-1])
            expected_target = derive_failure_within_n(df, n)
        else:
            expected_target = None

        if target_col in df.columns:
            # Validate target is binary
            if not set(df[target_col].unique()).issubset({0, 1, 0.0, 1.0}):
                raise DatasetValidationError(f"Supplied target column '{target_col}' must contain binary values (0 or 1).")
            df[target_col] = df[target_col].astype(int)

            # Cross-validate supplied target against derived expected target
            if expected_target is not None:
                mismatches = (df[target_col] != expected_target).sum()
                if mismatches > 0:
                    raise DatasetValidationError(
                        f"Supplied target column '{target_col}' has {mismatches} row mismatches with "
                        f"ground-truth target derived from 'is_failure' sequence."
                    )
        else:
            if expected_target is None:
                raise DatasetValidationError(f"Target column '{target_col}' could not be derived from dataset.")
            df[target_col] = expected_target
    else:
        # If is_failure is missing, target_col MUST exist and be binary
        if target_col not in df.columns:
            raise DatasetValidationError(
                f"Dataset missing 'is_failure' state column and required target column '{target_col}'."
            )
        if not set(df[target_col].unique()).issubset({0, 1, 0.0, 1.0}):
            raise DatasetValidationError(f"Supplied target column '{target_col}' must contain binary values (0 or 1).")
        df[target_col] = df[target_col].astype(int)

    return df


def split_trajectories_group_safe(
    df: pd.DataFrame,
    target_col: str,
    train_ratio: float = 0.70,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits DataFrame by unique trajectory IDs into group-disjoint train and validation subsets.
    Asserts set(train.trajectory_id).isdisjoint(set(val.trajectory_id)).
    Ensures both train and validation subsets contain both positive and negative target samples.
    """
    if "trajectory_id" not in df.columns:
        raise DatasetValidationError("Cannot perform group-safe split: missing 'trajectory_id' column.")

    unique_trajs = df["trajectory_id"].unique()
    n_trajs = len(unique_trajs)

    if n_trajs < 2:
        raise DatasetValidationError(
            f"Insufficient independent trajectories ({n_trajs}) for group-safe train/validation split. "
            f"At least 2 independent trajectories are required."
        )

    n_train = max(1, int(n_trajs * train_ratio))
    train_traj_ids = set(unique_trajs[:n_train])
    val_traj_ids = set(unique_trajs[n_train:])

    # Safeguard if int(n_trajs * train_ratio) selected all trajectories
    if not val_traj_ids:
        train_traj_ids = set(unique_trajs[:-1])
        val_traj_ids = set(unique_trajs[-1:])

    train_df = df[df["trajectory_id"].isin(train_traj_ids)].copy().reset_index(drop=True)
    val_df = df[df["trajectory_id"].isin(val_traj_ids)].copy().reset_index(drop=True)

    # Invariant assertion: disjoint trajectory ID sets
    assert train_traj_ids.isdisjoint(val_traj_ids), "Group split failed: train and validation trajectory IDs overlap."

    # Validate target diversity in both splits
    train_classes = set(train_df[target_col].unique())
    val_classes = set(val_df[target_col].unique())

    if len(train_classes) < 2:
        raise DatasetValidationError(
            f"Training trajectory partition lacks binary target diversity for '{target_col}' (classes present: {train_classes}). "
            f"Provide additional degradation trajectories."
        )

    if len(val_classes) < 2:
        raise DatasetValidationError(
            f"Validation trajectory partition lacks binary target diversity for '{target_col}' (classes present: {val_classes}). "
            f"Provide additional degradation trajectories."
        )

    return train_df, val_df
