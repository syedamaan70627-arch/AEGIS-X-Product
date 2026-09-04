"""
AEGIS-X Module 14 — Evidence-Calibrated Reliability Governance (ECRG)
Deterministic Evidence-Risk Learner & Trajectory-Aware Split Conformal Calibrator.

Mathematical Specifications:
1. Risk Learner: Fits L2-regularized logistic regression P(Y=1 | evidence x) on research-training split.
2. Nonconformity Score: s(x, y) = 1 - p_hat(y | x)
   - s(x, 1) = 1 - p_adverse(x)
   - s(x, 0) = p_adverse(x)
3. Split-Conformal Order-Statistic Quantile:
   - k = ceil((n + 1) * (1 - alpha))
   - q = sorted_scores[k - 1] (1-based order statistic, no interpolation)
   - Infeasible if k > n
4. Task Units:
   - STATIC_SELECTIVE_RISK: Independent sample calibration unit
   - TEMPORAL_GOVERNANCE: Independent engine trajectory calibration unit (N_cal = 20), S_i = max_t s(x_i,t, y_i,t)
5. Action Mapping:
   - {0}   -> CONTINUE
   - {0,1} -> WATCH
   - {1}   -> DEFER
   - {}    -> ESCALATE
"""

import math
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from aegis.governance.schemas import ECRGGovernanceAction


class InfeasibleAlphaError(ValueError):
    """Raised when the requested target risk alpha requires k > n calibration samples."""
    pass


class DeterministicRiskLearner:
    """
    Downstream Binary Evidence-Risk Learner for ECRG.
    Estimates p_adverse(x) = P(Y=1 | evidence x) using L2-regularized Logistic Regression.
    Preprocessing (StandardScaler) is fitted EXCLUSIVELY on the training split.
    """

    def __init__(self, random_seed: int = 42, c_penalty: float = 1.0):
        self.random_seed = random_seed
        self.c_penalty = c_penalty
        self.scaler: Optional[StandardScaler] = None
        self.model: Optional[LogisticRegression] = None
        self.feature_names: List[str] = []
        self.fitted: bool = False

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "DeterministicRiskLearner":
        """
        Fit feature scaler and logistic regression on training split.
        y_train: 1 = adverse outcome, 0 = non-adverse outcome.
        """
        if X_train.empty:
            raise ValueError("Training feature set X_train cannot be empty.")
        if len(X_train) != len(y_train):
            raise ValueError("Mismatch between X_train and y_train row counts.")
        if X_train.isna().any().any() or np.isinf(X_train.to_numpy()).any():
            raise ValueError("Training features contain NaN or Infinity.")

        self.feature_names = list(X_train.columns)
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_train)

        # Ensure y contains binary classes or handle single-class gracefully
        unique_y = np.unique(y_train)
        if len(unique_y) < 2:
            # Fallback for synthetic/single-class toy inputs
            self.model = LogisticRegression(penalty="l2", C=self.c_penalty, solver="lbfgs", random_state=self.random_seed)
            # Create synthetic tiny perturbation for fitting single class
            X_dummy = np.vstack([X_scaled, X_scaled + 1e-5])
            y_dummy = np.concatenate([np.full(len(X_scaled), unique_y[0]), np.full(len(X_scaled), 1 - unique_y[0])])
            self.model.fit(X_dummy, y_dummy)
        else:
            self.model = LogisticRegression(penalty="l2", C=self.c_penalty, solver="lbfgs", random_state=self.random_seed)
            self.model.fit(X_scaled, y_train)

        self.fitted = True
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict probability of adverse outcome P(Y=1 | x) for input features X.
        Returns array of shape (N,) containing p_adverse values.
        """
        if not self.fitted or self.scaler is None or self.model is None:
            raise RuntimeError("DeterministicRiskLearner must be fitted before predict_proba.")
        
        # Verify schema & feature order
        if list(X.columns) != self.feature_names:
            raise ValueError(f"Feature order/schema mismatch. Expected {self.feature_names}, got {list(X.columns)}")
        
        X_np = X.to_numpy()
        if np.isnan(X_np).any() or np.isinf(X_np).any():
            raise ValueError("Input features contain NaN or Infinity.")

        X_scaled = self.scaler.transform(X)
        proba = self.model.predict_proba(X_scaled)
        
        # Binary logistic regression output [p_safe, p_adverse]
        if proba.shape[1] == 2:
            return proba[:, 1]
        else:
            return proba[:, 0]

    def get_params_dict(self) -> Dict[str, Any]:
        """Export parameters for non-pickle serialization."""
        if not self.fitted or self.scaler is None or self.model is None:
            raise RuntimeError("Learner is not fitted.")
        return {
            "random_seed": self.random_seed,
            "c_penalty": self.c_penalty,
            "feature_names": self.feature_names,
            "scaler_mean": self.scaler.mean_.tolist(),
            "scaler_scale": self.scaler.scale_.tolist(),
            "coef": self.model.coef_.tolist(),
            "intercept": self.model.intercept_.tolist(),
            "classes": self.model.classes_.tolist(),
        }

    def load_params_dict(self, params: Dict[str, Any]) -> "DeterministicRiskLearner":
        """Load parameters from serialized dictionary."""
        self.random_seed = params["random_seed"]
        self.c_penalty = params["c_penalty"]
        self.feature_names = params["feature_names"]

        self.scaler = StandardScaler()
        self.scaler.mean_ = np.array(params["scaler_mean"])
        self.scaler.scale_ = np.array(params["scaler_scale"])
        self.scaler.var_ = self.scaler.scale_ ** 2
        self.scaler.n_samples_seen_ = 100  # Non-zero sentinel

        self.model = LogisticRegression(penalty="l2", C=self.c_penalty, solver="lbfgs", random_state=self.random_seed)
        self.model.coef_ = np.array(params["coef"])
        self.model.intercept_ = np.array(params["intercept"])
        self.model.classes_ = np.array(params["classes"])
        
        self.fitted = True
        return self


class TrajectorySplitConformalCalibrator:
    """
    Trajectory-Aware Split Conformal Calibrator for ECRG.
    Constructs auditable prediction sets C_alpha(x) with finite-sample order-statistic coverage guarantees.
    """

    def __init__(self, target_alpha: float = 0.05, learner: Optional[DeterministicRiskLearner] = None):
        if not (0.0 < target_alpha < 1.0):
            raise ValueError(f"Target alpha must be in (0, 1), got {target_alpha}")
        self.target_alpha = target_alpha
        self.learner = learner or DeterministicRiskLearner()
        self.calibrated_q: Optional[float] = None
        self.k_order_stat: Optional[int] = None
        self.n_cal_units: int = 0
        self.finite_sample_resolution: float = 0.0
        self.task_type: str = "TEMPORAL_GOVERNANCE"
        self.calibration_scores: List[float] = []

    @staticmethod
    def compute_nonconformity_score(p_adverse: float, y_true: int) -> float:
        """
        Compute nonconformity score s(x, y) = 1 - p_hat(y | x).
        - If y_true == 1: s = 1 - p_adverse = p_safe
        - If y_true == 0: s = 1 - (1 - p_adverse) = p_adverse
        """
        if p_adverse is None or math.isnan(float(p_adverse)) or math.isinf(float(p_adverse)):
            raise ValueError(f"p_adverse score cannot be NaN, Infinity, or None, got {p_adverse}.")
        if y_true == 1:
            return float(1.0 - p_adverse)
        elif y_true == 0:
            return float(p_adverse)
        else:
            raise ValueError(f"Invalid y_true label {y_true}. Must be 0 or 1.")

    @staticmethod
    def compute_order_statistic_quantile(scores: List[float], alpha: float) -> Tuple[float, int, int]:
        """
        Compute exact 1-based order-statistic quantile without interpolation.
        Returns (q, k, n).
        Formula:
          n = len(scores)
          k = ceil((n + 1) * (1 - alpha))
          If k > n: raise InfeasibleAlphaError
          q = sorted_scores[k - 1]
        """
        n = len(scores)
        if n == 0:
            raise ValueError("Calibration score vector is empty.")
        
        k = math.ceil((n + 1) * (1.0 - alpha))
        if k > n:
            raise InfeasibleAlphaError(
                f"Requested alpha={alpha} is infeasible for n={n} calibration units. "
                f"Required k-th order statistic index k={k} exceeds n={n}. "
                f"Minimum feasible alpha for n={n} is 1/(n+1) = {1.0 / (n + 1):.4f}."
            )
        
        sorted_scores = sorted(scores)
        q = float(sorted_scores[k - 1])
        return q, k, n

    def calibrate_static(
        self,
        X_cal: pd.DataFrame,
        y_cal: pd.Series,
    ) -> float:
        """
        Calibrate on STATIC_SELECTIVE_RISK dataset where each row is an independent sample unit.
        y_cal: 1 = prediction error (adverse), 0 = correct (non-adverse).
        """
        self.task_type = "STATIC_SELECTIVE_RISK"
        p_adverse_array = self.learner.predict_proba(X_cal)
        
        scores = []
        for i in range(len(X_cal)):
            p_adv = float(p_adverse_array[i])
            y_t = int(y_cal.iloc[i])
            scores.append(self.compute_nonconformity_score(p_adv, y_t))

        q, k, n = self.compute_order_statistic_quantile(scores, self.target_alpha)
        self.calibrated_q = q
        self.k_order_stat = k
        self.n_cal_units = n
        self.finite_sample_resolution = 1.0 / (n + 1.0)
        self.calibration_scores = scores
        return q

    def calibrate_temporal(
        self,
        df_cal: pd.DataFrame,
        trajectory_col: str = "trajectory_id",
        target_col: str = "failure_within_horizon",
        feature_cols: Optional[List[str]] = None,
    ) -> float:
        """
        Calibrate on TEMPORAL_GOVERNANCE dataset where each independent unit is ONE complete engine trajectory.
        Computes trajectory-max nonconformity score S_i = max_t s(x_i,t, y_i,t).
        """
        self.task_type = "TEMPORAL_GOVERNANCE"
        if trajectory_col not in df_cal.columns:
            raise ValueError(f"Trajectory column '{trajectory_col}' not found in df_cal.")
        if target_col not in df_cal.columns:
            raise ValueError(f"Target column '{target_col}' not found in df_cal.")

        cols_to_use = feature_cols or self.learner.feature_names
        X_cal = df_cal[cols_to_use]
        p_adverse_array = self.learner.predict_proba(X_cal)

        trajectory_scores = []
        unique_trajectories = df_cal[trajectory_col].unique()

        for traj_id in unique_trajectories:
            traj_mask = (df_cal[trajectory_col] == traj_id).to_numpy()
            traj_indices = np.where(traj_mask)[0]
            
            traj_step_scores = []
            for idx in traj_indices:
                p_adv = float(p_adverse_array[idx])
                y_t = int(df_cal[target_col].iloc[idx])
                traj_step_scores.append(self.compute_nonconformity_score(p_adv, y_t))

            # Trajectory-max aggregation across all eligible steps
            traj_max_score = float(max(traj_step_scores))
            trajectory_scores.append(traj_max_score)

        q, k, n = self.compute_order_statistic_quantile(trajectory_scores, self.target_alpha)
        self.calibrated_q = q
        self.k_order_stat = k
        self.n_cal_units = n
        self.finite_sample_resolution = 1.0 / (n + 1.0)
        self.calibration_scores = trajectory_scores
        return q

    def predict_conformal_set(self, X_step: pd.DataFrame) -> Tuple[List[int], float, Dict[str, float]]:
        """
        Predict split conformal prediction set C_alpha(x) = { y in {0,1} : s(x, y) <= q }.
        Returns (prediction_set, p_adverse, nonconformity_details).
        """
        if self.calibrated_q is None:
            raise RuntimeError("Calibrator is not calibrated. Call calibrate_static or calibrate_temporal first.")

        p_adverse_arr = self.learner.predict_proba(X_step)
        p_adverse = float(p_adverse_arr[0])

        s_y0 = float(p_adverse)          # s(x, 0) = 1 - p_safe = p_adverse
        s_y1 = float(1.0 - p_adverse)    # s(x, 1) = 1 - p_adverse

        prediction_set = []
        if s_y0 <= self.calibrated_q:
            prediction_set.append(0)
        if s_y1 <= self.calibrated_q:
            prediction_set.append(1)

        details = {
            "s_y0": s_y0,
            "s_y1": s_y1,
            "quantile_q": float(self.calibrated_q),
            "k_order_stat": self.k_order_stat,
            "n_cal_units": self.n_cal_units,
            "alpha": self.target_alpha,
            "resolution": self.finite_sample_resolution,
        }

        return prediction_set, p_adverse, details

    @staticmethod
    def map_prediction_set_to_raw_action(prediction_set: List[int]) -> ECRGGovernanceAction:
        """
        Raw Governance Action Mapping according to Section 7:
        - {0}   -> CONTINUE
        - {0,1} -> WATCH
        - {1}   -> DEFER
        - {}    -> ESCALATE
        """
        set_repr = set(prediction_set)
        if set_repr == {0}:
            return ECRGGovernanceAction.CONTINUE
        elif set_repr == {0, 1}:
            return ECRGGovernanceAction.WATCH
        elif set_repr == {1}:
            return ECRGGovernanceAction.DEFER
        elif set_repr == set():
            return ECRGGovernanceAction.ESCALATE
        else:
            raise ValueError(f"Invalid prediction set contents {prediction_set}")
