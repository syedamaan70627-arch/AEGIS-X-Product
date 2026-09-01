"""
AEGIS-X Early Warning Horizon Evaluator Module.

Evaluates trajectory-level lead times, warning coverage, and false trajectory warning rates
for Module 10.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from aegis.core.contracts import (
    TrajectoryWarningResult,
    WarningHorizon,
)


class EarlyWarningHorizonEvaluator:
    """
    Evaluator for state-level and trajectory-level early warning metrics.
    """

    @staticmethod
    def evaluate_trajectories(
        df_results: pd.DataFrame,
        horizon_val: int = 3,
        threshold: float = 0.46,
        trajectory_col: str = "trajectory_id",
        failure_col: str = "Failure_Rate",
        failure_boundary: float = 0.10,
    ) -> Tuple[Dict[str, Any], List[TrajectoryWarningResult]]:
        """
        Evaluates trajectory-level warning lead times and false warning rates.
        """
        horizon = WarningHorizon(value=horizon_val, unit="controlled_degradation_states")
        trajectory_results: List[TrajectoryWarningResult] = []

        grouped = df_results.groupby(trajectory_col) if trajectory_col in df_results.columns else [("default", df_results)]

        failing_traj_count = 0
        warned_failing_count = 0
        non_failing_traj_count = 0
        false_warning_count = 0
        lead_steps_list: List[int] = []

        for traj_id, group in grouped:
            group_sorted = group.reset_index(drop=True)
            if failure_col in group_sorted.columns and failure_col not in {"Failure_Rate", "Failure_Onset_Next"} and not failure_col.startswith("Failure_Within_"):
                if group_sorted[failure_col].dtype in [float, np.float64, np.float32]:
                    failures = (group_sorted[failure_col] >= failure_boundary).to_numpy()
                else:
                    failures = (group_sorted[failure_col] == 1).to_numpy()
            elif "is_failure" in group_sorted.columns:
                failures = (group_sorted["is_failure"] == 1).to_numpy()
            elif "Failure_Rate" in group_sorted.columns:
                failures = (group_sorted["Failure_Rate"] >= failure_boundary).to_numpy()
            else:
                failures = np.zeros(len(group_sorted), dtype=bool)

            warnings = (group_sorted["warning_probability"] >= threshold).to_numpy()

            eventually_fails = bool(np.any(failures))

            if eventually_fails:
                failing_traj_count += 1
                fail_idx = int(np.argmax(failures))

                # Check warnings before or at failure boundary
                warn_indices = np.where(warnings[: fail_idx + 1])[0]
                if len(warn_indices) > 0:
                    first_warn_idx = int(warn_indices[0])
                    lead = fail_idx - first_warn_idx
                    warned_failing_count += 1
                    lead_steps_list.append(lead)

                    traj_res = TrajectoryWarningResult(
                        trajectory_id=traj_id,
                        eventually_fails=True,
                        first_warning_state_index=first_warn_idx,
                        failure_state_index=fail_idx,
                        lead_steps=lead,
                        is_early_warning=bool(lead > 0),
                        is_false_trajectory_warning=False,
                        details={"horizon": horizon.value, "unit": horizon.unit},
                    )
                else:
                    traj_res = TrajectoryWarningResult(
                        trajectory_id=traj_id,
                        eventually_fails=True,
                        failure_state_index=fail_idx,
                        is_early_warning=False,
                        is_false_trajectory_warning=False,
                        details={"horizon": horizon.value, "unit": horizon.unit},
                    )
            else:
                non_failing_traj_count += 1
                warn_triggered = bool(np.any(warnings))
                if warn_triggered:
                    false_warning_count += 1

                traj_res = TrajectoryWarningResult(
                    trajectory_id=traj_id,
                    eventually_fails=False,
                    is_early_warning=False,
                    is_false_trajectory_warning=warn_triggered,
                    details={"horizon": horizon.value, "unit": horizon.unit},
                )

            trajectory_results.append(traj_res)

        coverage = float(warned_failing_count / failing_traj_count) if failing_traj_count > 0 else 0.0
        mean_lead = float(np.mean(lead_steps_list)) if lead_steps_list else 0.0
        median_lead = float(np.median(lead_steps_list)) if lead_steps_list else 0.0
        false_warning_rate = float(false_warning_count / non_failing_traj_count) if non_failing_traj_count > 0 else 0.0

        traj_metrics = {
            "failing_trajectories": failing_traj_count,
            "warned_failing_trajectories": warned_failing_count,
            "early_warning_coverage": coverage,
            "mean_lead_steps": mean_lead,
            "median_lead_steps": median_lead,
            "non_failing_trajectories": non_failing_traj_count,
            "false_trajectory_warnings": false_warning_count,
            "false_trajectory_warning_rate": false_warning_rate,
            "lead_time_unit": horizon.unit,
        }

        return traj_metrics, trajectory_results
