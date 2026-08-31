# AEGIS-X Scientific Regression Report

This document records the scientific comparison between the production implementations (`aegis/`) and the research notebook (`research_source/AEGIS_X_01_Baseline.ipynb`).

---

## 1. Reproduction Status Overview

| Component | Research Notebook Module | Production Implementation | Reproduction Status | Tolerance / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Feature Scaling** | Module 1 (Cells 7, 19) | `FeaturePreprocessor` | **Successfully Reproduced** | Exact match (`StandardScaler`) |
| **Mahalanobis Distance** | Module 2 (Cell 23) | `OODDetector(method='mahalanobis')` | **Successfully Reproduced** | Exact formula match ($10^{-5}$ float tolerance) |
| **Isolation Forest OOD** | Module 2 (Cell 25) | `OODDetector(method='isolation_forest')` | **Successfully Reproduced** | Exact hyperparameter match (`n_estimators=100, random_state=42`) |
| **Empirical Percentile Risk** | Module 2 (Cell 26) | `ReferenceState.get_empirical_percentiles()` | **Successfully Reproduced** | Exact empirical CDF percentile transformation |
| **Predictive Entropy** | Module 3 (Cell 41) | `UncertaintyEstimator(method='predictive_entropy')` | **Successfully Reproduced** | Exact match $H(p) = -\sum p_c \log_2(p_c + 10^{-12})$ |
| **Platt Calibration** | Module 3 (Cell 44) | `PlattCalibrator` | **Successfully Reproduced** | Exact Logistic Regression logit mapping |
| **KS Distribution Test** | Module 4 (Cell 63) | `DriftDetector(method='ks_test')` | **Successfully Reproduced** | Exact `scipy.stats.ks_2samp` statistic & p-value |
| **ADWIN Streaming Drift** | Module 4 (Cell 62) | `ADWINWrapper` | **Successfully Reproduced** | Exact `river.drift.ADWIN(delta=0.002)` wrapper |
| **Module 5 Naive Fusion** | Module 5 (Cells 86–112) | `OriginalFusion` | **Successfully Reproduced** | Replicates linear interaction model & negative collapse findings |
| **Module 6 Stress Suite** | Module 6 (Cells 114–128) | `gaussian_noise_stress`, `feature_dropout_stress`, `feature_permutation_stress`, `combined_stress` | **Successfully Reproduced** | Operates on copies; exact corruptions & initial failure preserved |
| **Module 6R Robust Fusion** | Module 6R (Cells 129–140) | `StressRobustFusion` | **Successfully Reproduced** | Group-aware splitting by stress run; robust interaction meta-fusion |
| **Module 7 Fault Injection** | Module 7 (Cells 140–158) | `FaultInjector` | **Successfully Reproduced** | 5 families: Feature Bias, Gain Error, Stuck-At, Channel Swap, Sign Inversion |
| **Module 7 Failure Discovery** | Module 7 (Cells 145–155) | `FailureDiscoveryEngine` | **Successfully Reproduced** | Label-aware vs label-free mode; confirmed silent failure identification |
| **Module 8 Naive Clustering** | Module 8 (Cells 159–168) | Historical Baseline | **Preserved (Negative Result)** | Replicates degenerate observation-level clustering (>90% cluster imbalance) |
| **Module 8R Failure Memory** | Module 8R (Cells 169–198) | `FailureMemory`, `FailureMemoryMatcher` | **Successfully Reproduced** | Condition-profile clustering ($K=3$, silhouette $\approx 0.3616$, stability ARI $= 1.0$) |
| **Module 9 Naive Predictor** | Module 9 (Cells 199–205) | Historical Baseline | **Preserved (Partial Result)** | Replicates weak pre-failure onset recall ($\approx 0.4000$) |
| **Module 9R Failure Predictor** | Module 9R (Cells 206–214) | `FailurePredictor`, `ValidationThresholdSelector` | **Successfully Reproduced** | Evaluated RF, GB, LR; selected `RandomForestClassifier(n_estimators=100, random_state=42)` on validation F1 (AUROC $\approx 0.8286$, Recall $\approx 0.8000$, F1 $\approx 0.7273$) |
| **Module 10 Early Warning** | Module 10 (Cells 215–220) | `EarlyWarningEngine`, `EarlyWarningHorizonEvaluator` | **Successfully Reproduced (Promising / Partial)** | Dynamic Multi-Signal; $H^*=3$ states; validation thresholding; $100\%$ coverage on failing trajectories, but $100\%$ false warning on non-failing sample |
| **Module 11 Ablation Study** | Module 11 (Cell 217) | `AblationEvaluator` | **Successfully Reproduced** | Evaluates Full vs No-OOD, No-Uncertainty, No-Drift, and Static; preserves positive No-Drift delta ($+0.0123$) and Uncertainty sensitivity (drop $-0.2329$) |
| **Module 12 Cross-Domain** | Module 12 (Cell 218) | `CrossDomainEvaluator`, `load_breast_cancer_fixture`, `load_digits_parity_fixture` | **Successfully Reproduced** | Evaluated Breast Cancer & Digits Parity (target leakage prevented); mean fusion AUROC $\approx 0.8009$, mean Spearman $\approx 0.7923$, mean unseen AUROC $\approx 0.7708$, fusion wins $2/2$ |
| **Module 13 Multi-Seed** | Module 13 (Cell 219) | `MultiSeedEvaluator`, `bootstrap_mean_ci`, `calculate_paired_gain` | **Successfully Reproduced** | Evaluated 20/20 runs across 10 seeds; mean fusion AUROC $\approx 0.7849$, paired AUPR gain $+0.0006$ with 95% CI $[-0.0082, +0.0084]$ (includes zero -> fusion superiority statistically inconclusive) |
| **Colab Mount Paths** | Header / Setup | `storage/models/`, `storage/datasets/` | **Refactored (By Design)** | Hardcoded `/content/drive` paths removed from production |

---

## 2. Detailed Reproduction Verification

### A. OOD Distance & Isolation Scores
- **Notebook Implementation**: Used Mahalanobis distance with regularized inverse covariance matrix and `IsolationForest(n_estimators=100, contamination=0.01)`.
- **Production Result**: Verified in `tests/test_ood.py`. In-distribution evaluation scores yield low risk ($R_{OOD} < 0.2$), while shifted evaluation samples yield high risk ($R_{OOD} > 0.8$).

### B. Predictive Entropy & Platt Calibration
- **Notebook Implementation**: Used base-2 logarithm predictive entropy $H(p) = -\sum p \log_2 p$ and Platt calibration fitted on a validation split.
- **Production Result**: Verified in `tests/test_uncertainty.py`. Edge probabilities $[1.0, 0.0]$ yield $0.0$ bits entropy; balanced probabilities $[0.5, 0.5]$ yield $1.0$ bit entropy. Models without `predict_proba()` gracefully return `ReliabilityStatus.NOT_AVAILABLE`.

### C. Feature Distribution Drift Tests
- **Notebook Implementation**: Used two-sample Kolmogorov-Smirnov tests and River ADWIN streaming detectors.
- **Production Result**: Verified in `tests/test_drift.py`. Nominal data yields `drift_detected = False`; mean-shifted feature distributions yield `drift_detected = True`. Degenerate features with std = 0 emit warnings without crashing.

### D. Module 5 & 6 Fusion and Stress Testing
- **Notebook Implementation**: Naive linear interaction fusion degraded under severe noise (Module 6 negative result).
- **Production Result**: Verified in `tests/test_fusion.py`, `tests/test_stress.py`, and `tests/test_stress_robust_fusion.py`. `OriginalFusion` logs a warning regarding naive fusion generalization limits, while `StressRobustFusion` uses group-aware splits by base sample ID to prevent temporal leakage between stress runs.

### E. Module 7 Structured Fault Injection & Failure Discovery
- **Notebook Implementation**: Evaluated 5 fault families across severity levels $0.05 \dots 0.50$ with 3 replicates. Reported historical metrics: Spearman $\rho \approx 0.9771$ between risk and failure rate, total failure events $\approx 6202$, silent failure events $\approx 864$, and silent failure fraction $\approx 13.93\%$.
- **Production Result**: Verified in `tests/test_faults.py` and `tests/test_failure_discovery.py`. Enforces strict copy safety, label-free vs label-aware separation, and confirmed silent failure identification ($\text{Actual Failure} == 1 \quad \text{AND} \quad \text{High-Risk Warning} == 0$).

### F. Module 8 & 8R Failure Signatures & Failure Memory
- **Notebook Implementation**: Original observation-level clustering yielded a degenerate solution (>90% cluster imbalance). Module 8R refined clustering by aggregating events into condition profiles (`mean_ood_risk`, `mean_uncertainty`, `mean_drift_score`, `mean_fused_risk`, `failure_rate`, `silent_failure_rate`), achieving $K=3$ cluster balance, silhouette score $\approx 0.3616$, and stability ARI $= 1.0$ across 10 random seeds. Fault labels were excluded from clustering inputs and used strictly post-hoc.
- **Production Result**: Verified in `tests/test_failure_signatures.py` and `tests/test_failure_memory.py`. Implements `FailureMemory` and `FailureMemoryMatcher`, preserving fit vs match separation and pre-fitted scaling. Avoids false root-cause claims in all result dataclasses.

### G. Module 9 & 9R Failure Prediction & Validation Thresholding
- **Notebook Implementation & Model Selection Clarification**:
  - Candidate models evaluated: `RandomForestClassifier(n_estimators=100, random_state=42)`, `GradientBoostingClassifier(n_estimators=100, random_state=42)`, and `LogisticRegression(class_weight="balanced", random_state=42)`.
  - Validation-only model selection rule: Evaluated probability scores on `prediction_select_df` (`Replicate 1` / Validation split) using `select_best_threshold()` to maximize F1 score. The candidate model achieving the highest validation F1 score and onset recall $\ge 0.60$ was selected as `BEST_PREDICTOR`.
  - Final selected model in research notebook: `RandomForestClassifier(n_estimators=100, random_state=42)` with `dynamic` feature set ($S_{ood}, U, D, R_{fused}, \Delta S_{ood}, \Delta U, \Delta D, \Delta R_{fused}$).
  - Final held-out evaluation (`Replicate 2`) achieved AUROC $\approx 0.8286$, AUPR $\approx 0.7548$, Recall $\approx 0.8000$, Precision $\approx 0.6667$, F1 $\approx 0.7273$, and False Warning Rate $\approx 0.1429$.
- **Production Result**: Verified in `tests/test_failure_prediction.py`, `tests/test_prediction_threshold.py`, and `tests/test_prediction_temporal_safety.py`. Guarantees temporal safety (backward-looking deltas $\Delta f_t = f_t - f_{t-1}$), excludes severity from predictors, and enforces validation-only thresholding (test labels CANNOT alter threshold).

### H. Module 10 Temporal Early Warning & Lead Time Diagnostics
- **Notebook Implementation**: Evaluated Dynamic Multi-Signal feature configuration across multi-state horizons $H \in \{1, 2, 3, 5, 10\}$. Selected $H^*=3$ controlled degradation states and threshold $T_{warn} \approx 0.46$ on validation split under false warning cap $\le 0.20$. Final state-level held-out metrics: AUROC $\approx 0.8182$, AUPR $\approx 0.8832$, Recall $\approx 0.7273$, Precision $\approx 0.8000$, F1 $\approx 0.7619$. Trajectory-level metrics: 4/4 failing trajectories received early warnings ($100\%$ coverage, mean lead $\approx 2.25$ states), but the single held-out non-failing trajectory ALSO triggered a warning ($100\%$ false trajectory warning rate).
- **Production Result**: Verified in `tests/test_early_warning.py`, `tests/test_warning_horizon.py`, `tests/test_warning_temporal_safety.py`, and `tests/test_trajectory_warning.py`. Enforces horizon unit `controlled_degradation_states` (never clock time), validation-only threshold selection, and explicitly reports false warning rates on non-failing trajectories.

### I. Module 11 Component Ablation Study
- **Notebook Implementation**: Re-fitted model pipelines for each ablated feature set (`FULL`, `NO_OOD`, `NO_UNCERTAINTY`, `NO_DRIFT`, `STATIC`) on `train_df`, selected warning thresholds on `validation_df` under false warning cap $\le 0.20$, and evaluated final held-out metrics. Reported historical metrics: `FULL` AUPR $\approx 0.8884$; `NO_UNCERTAINTY` AUPR $\approx 0.6555$ (drop of $-0.2329$, proving Uncertainty was the most performance-sensitive component on this benchmark); `NO_OOD` AUPR $\approx 0.8884$ (minimal delta); `NO_DRIFT` AUPR $\approx 0.9007$ (positive delta $+0.0123$, proving removing Drift slightly improved AUPR on this benchmark). Dynamic features improved AUPR by $+0.0035$ and F1 by $+0.0952$.
- **Production Result**: Verified in `tests/test_ablation.py`. Implements `AblationEvaluator` under `aegis/evaluation/`, preserving fair train/validation/final separation, validation-only threshold selection, signed deltas, and positive No-Drift delta support without automatic component pruning.

### J. Module 12 Real Cross-Domain Validation
- **Notebook Implementation**: Evaluated AEGIS-X reliability framework across Breast Cancer Wisconsin (569 samples, 30 features) and Digits Parity (1797 samples, 64 pixel features transformed into Even vs Odd binary target). Original digit identity was excluded from predictors. Reported metrics: Breast Cancer accuracy $\approx 0.9737$, fusion AUROC $\approx 0.8404$; Digits Parity accuracy $\approx 0.9056$, fusion AUROC $\approx 0.7613$. Aggregate mean fusion AUROC $\approx 0.8009$, mean risk/failure Spearman correlation $\approx 0.7923$, mean unseen-family AUROC $\approx 0.7708$. Fusion beat best individual signal in 2 out of 2 domains in this single-run experiment. Preserved limitation: Cross-domain failure ranking was strong, but cross-domain early warning lead boundaries exhibited missing, zero, or negative/late warning steps on Digits Parity.
- **Production Result**: Verified in `tests/test_research_datasets.py` and `tests/test_cross_domain.py`. Implements `load_breast_cancer_fixture()`, `load_digits_parity_fixture()`, and `CrossDomainEvaluator` under `aegis/evaluation/`, strictly preventing target leakage and preserving early-warning cross-domain limitations.

### K. Module 13 Final Multi-Seed Validation & Bootstrap Confidence Intervals
- **Notebook Implementation**: Evaluated 20 independent experiments across 10 random seeds (`[42, 101, 202, 303, 404, 505, 606, 707, 808, 909]`) and 2 real domains (`Breast Cancer Wisconsin` and `Digits Parity`). All 20/20 completed. Severity was excluded as an input feature. Computed 95% non-parametric bootstrap percentile confidence intervals. Reported metrics:
  - Mean Fusion AUROC: $\approx 0.7849$, 95% CI: $[0.7589, 0.8117]$.
  - Mean Risk/Failure Spearman: $\approx 0.5768$, 95% CI: $[0.5128, 0.6368]$.
  - Mean Unseen-Family AUROC: $\approx 0.7524$, 95% CI: $[0.7231, 0.7814]$.
  - Mean Paired Fusion AUPR Gain: $\Delta AUPR \approx +0.0006$, 95% CI: $[-0.0082, +0.0084]$.
  - Fusion Win Rate: 70.0% (14/20 wins).
  - Domain-Level Gains: Breast Cancer Wisconsin mean gain $\approx -0.0079$, Digits Parity mean gain $\approx +0.0091$.
  - Early Warning Reproducibility: 53 measurable fault/run boundaries, 30 positive early-warning leads (56.6%), 13 late warnings (24.53%).
  - Statistical Interpretation & Scientific Verdict: `verdict = "ROBUST FRAMEWORK / MIXED FUSION EVIDENCE"`. Because the 95% bootstrap confidence interval for paired AUPR gain includes zero ($[-0.0082, +0.0084]$), fusion superiority over the strongest individual signal is **STATISTICALLY INCONCLUSIVE** and domain-dependent.
- **Production Result**: Verified in `tests/test_bootstrap.py`, `tests/test_paired_fusion.py`, and `tests/test_multiseed.py`. Implements `bootstrap_mean_ci`, `calculate_paired_gain`, and `MultiSeedEvaluator` under `aegis/evaluation/`. Preserves exact verdict and all 8 major negative research findings.

---

## 3. Discrepancies & Deviations from Colab State

1. **Path Dependence**:
   - **Colab**: Hardcoded access to `/content/drive/MyDrive/AEGIS-X/`.
   - **Production**: Uses `storage/models/`, `storage/datasets/`, and `storage/results/`.
   - **Justification**: Production software must run independently of Google Colab environment infrastructure.

2. **Input Mutability**:
   - **Colab**: Modified Pandas DataFrames in-place in some exploratory cells.
   - **Production**: Enforces strict input-copy safety; `analyze()`, `transform()`, stress generators, fault injectors, ablation evaluators, cross-domain evaluators, and multi-seed evaluators never mutate input DataFrames or numpy arrays.
