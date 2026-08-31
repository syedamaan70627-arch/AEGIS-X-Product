"""
AEGIS-X Concept & Feature Distribution Drift Detector Module.

Migrates Module 4 research logic: Kolmogorov-Smirnov test, Population Stability Index (PSI),
Binned Chi-Square test, ADWIN sequential streaming, and degenerate feature handling.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy.stats import chisquare, ks_2samp

from aegis.core.contracts import DriftResult, ReliabilityStatus
from aegis.core.exceptions import DatasetValidationError
from aegis.core.reference_state import ReferenceState
from aegis.drift.adwin_wrapper import ADWINWrapper


class DriftDetector:
    """
    Label-free feature distribution drift detector implementing validated KS-test,
    PSI, Chi-Square, and ADWIN streaming change detection.
    """

    def __init__(
        self,
        method: str = "ks_test",
        alpha: float = 0.05,
        adwin_delta: float = 0.002,
    ) -> None:
        if method not in ("ks_test", "psi", "chi_square", "adwin"):
            raise DatasetValidationError(
                f"Unsupported drift method '{method}'. Supported methods: 'ks_test', 'psi', 'chi_square', 'adwin'."
            )
        self.method: str = method
        self.alpha: float = alpha
        
        self.reference_state: Optional[ReferenceState] = None
        self.adwin_wrapper: ADWINWrapper = ADWINWrapper(delta=adwin_delta)
        self.is_fitted: bool = False

    def fit(
        self,
        reference_data: Union[pd.DataFrame, np.ndarray, ReferenceState],
        feature_names: Optional[List[str]] = None,
    ) -> "DriftDetector":
        """Fits reference distribution state on nominal training/reference data."""
        if isinstance(reference_data, ReferenceState):
            if not reference_data.is_fitted:
                raise DatasetValidationError("Provided ReferenceState is not fitted.")
            self.reference_state = reference_data
        else:
            self.reference_state = ReferenceState(feature_names=feature_names)
            self.reference_state.fit(reference_data)

        if self.reference_state.feature_names is not None:
            self.adwin_wrapper.initialize_features(self.reference_state.feature_names)

        self.is_fitted = True
        return self

    def _compute_psi_feature(
        self, ref_arr: np.ndarray, eval_arr: np.ndarray, n_bins: int = 10, eps: float = 1e-4
    ) -> float:
        """Computes Population Stability Index (PSI) for a single feature."""
        # Determine quantiles on reference
        percentiles = np.linspace(0, 100, n_bins + 1)
        bins = np.percentile(ref_arr, percentiles)
        bins = np.unique(bins)
        if len(bins) < 2:
            return 0.0

        ref_counts, _ = np.histogram(ref_arr, bins=bins)
        eval_counts, _ = np.histogram(eval_arr, bins=bins)

        ref_pct = np.maximum(ref_counts / len(ref_arr), eps)
        eval_pct = np.maximum(eval_counts / len(eval_arr), eps)

        psi = np.sum((eval_pct - ref_pct) * np.log(eval_pct / ref_pct))
        return float(psi)

    def analyze(self, evaluation_data: Union[pd.DataFrame, np.ndarray]) -> DriftResult:
        """Analyzes evaluation feature distribution against nominal reference state without mutating input or using labels."""
        if not self.is_fitted or self.reference_state is None:
            return DriftResult(
                status=ReliabilityStatus.NOT_AVAILABLE,
                method=self.method,
                warnings=["DriftDetector must be fitted before running analyze()."],
                limitations=["No reference state fitted."],
            )

        try:
            # Transform and realign evaluation data without mutating input
            eval_scaled = self.reference_state.preprocessor.transform(evaluation_data)
            ref_scaled = self.reference_state.X_ref_scaled
            feature_names = self.reference_state.feature_names or [
                f"feature_{i}" for i in range(eval_scaled.shape[1])
            ]

            feature_flags: Dict[str, bool] = {}
            feature_pvals: Dict[str, float] = {}
            feature_stats: Dict[str, float] = {}
            warnings_list: List[str] = []

            for i, feat_name in enumerate(feature_names):
                ref_col = ref_scaled[:, i]
                eval_col = eval_scaled[:, i]

                # Check for degenerate/constant features
                if np.std(ref_col) < 1e-12 or np.std(eval_col) < 1e-12:
                    warnings_list.append(f"Feature '{feat_name}' is constant or has near-zero variance; skipped drift test.")
                    feature_flags[feat_name] = False
                    feature_pvals[feat_name] = 1.0
                    feature_stats[feat_name] = 0.0
                    continue

                if self.method == "ks_test":
                    ks_res = ks_2samp(ref_col, eval_col)
                    stat = float(ks_res.statistic)
                    pval = float(ks_res.pvalue)
                    flag = bool(pval < self.alpha)

                elif self.method == "psi":
                    stat = self._compute_psi_feature(ref_col, eval_col)
                    pval = 0.0 if stat > 0.25 else (0.05 if stat > 0.1 else 0.5)
                    flag = bool(stat >= 0.1)

                elif self.method == "chi_square":
                    # Binned Chi-Square test
                    bins = np.linspace(np.min(ref_col), np.max(ref_col) + 1e-6, 10)
                    ref_counts, _ = np.histogram(ref_col, bins=bins)
                    eval_counts, _ = np.histogram(eval_col, bins=bins)
                    # Scale counts for test
                    eval_counts_norm = eval_counts * (np.sum(ref_counts) / np.maximum(np.sum(eval_counts), 1))
                    chi_res = chisquare(eval_counts_norm + 1e-5, f_exp=ref_counts + 1e-5)
                    stat = float(chi_res.statistic)
                    pval = float(chi_res.pvalue)
                    flag = bool(pval < self.alpha)

                else:  # ADWIN batch approximation
                    batch_flags = self.adwin_wrapper.update_batch(eval_scaled, feature_names)
                    latest_flags = batch_flags[-1] if batch_flags else {}
                    flag = bool(latest_flags.get(feat_name, False))
                    stat = 1.0 if flag else 0.0
                    pval = 0.0 if flag else 1.0

                feature_flags[feat_name] = flag
                feature_pvals[feat_name] = pval
                feature_stats[feat_name] = stat

            # Compute aggregate drift ratio
            drifted_count = sum(1 for f in feature_flags.values() if f)
            total_count = len(feature_flags) if feature_flags else 1
            aggregate_drift_score = float(drifted_count / total_count)
            drift_detected = bool(aggregate_drift_score > 0.2)

            return DriftResult(
                status=ReliabilityStatus.AVAILABLE,
                method=self.method,
                feature_drift_flags=feature_flags,
                feature_p_values=feature_pvals,
                feature_statistics=feature_stats,
                aggregate_drift_score=aggregate_drift_score,
                drift_detected=drift_detected,
                warnings=warnings_list,
                limitations=[
                    "Label-free distribution drift detection monitors feature space P(X) shift.",
                    "Distribution drift does NOT guarantee concept drift P(Y|X) shift.",
                ],
            )
        except Exception as e:
            return DriftResult(
                status=ReliabilityStatus.ERROR,
                method=self.method,
                warnings=[f"Drift analysis failed: {str(e)}"],
                limitations=["Execution error occurred during drift detection."],
            )

    def update_stream(self, sample_dict: Dict[str, float]) -> Dict[str, bool]:
        """Sequentially updates ADWIN streaming detector with a single new streaming sample dictionary."""
        return self.adwin_wrapper.update_sample(sample_dict)
