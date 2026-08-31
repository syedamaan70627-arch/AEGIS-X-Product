# AEGIS-X Backend Reliability Engine Architecture

This document describes the core architecture, data flow, calibration governance, fusion engines, stress testing lab, fault injection lab, failure memory, failure prediction, temporal early warning, component ablation, cross-domain validation, multi-seed statistical validation, and scientific boundaries of AEGIS-X.

---

## 1. High-Level Workflows

### Workflow A: Normal Monitoring Architecture

```
Reference Data (Nominal X_ref)
          │
          ▼
┌──────────────────────────────────────┐
│ Fit Reference Reliability State      │
│ - StandardScaler (Normalizer)        │
│ - Mean Vector (μ) & Covariance (Σ)   │
│ - Empirical CDF Risk Distributions   │
│ - Reference Feature Distribution     │
└──────────────────────────────────────┘
          │
          ▼
Evaluation Data (Unlabeled X_eval)
          │
          ├────────────────────────┬────────────────────────┐
          ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   OOD Engine     │    │Uncertainty Engine│    │   Drift Engine   │
│  (Mahalanobis /  │    │ (Predictive      │    │(Kolmogorov-      │
│ IsolationForest) │    │  Entropy H(p))   │    │ Smirnov / ADWIN) │
└──────────────────┘    └──────────────────┘    └──────────────────┘
          │                        │                        │
          └────────────────────────┼────────────────────────┘
                                   │
                                   ▼
                   ┌────────────────────────────────┐
                   │  Core Reliability Signals      │
                   │  (S_ood, U, D)                 │
                   └────────────────────────────────┘
                                   │
                                   ▼
                   ┌────────────────────────────────┐
                   │  Fusion Engine (Module 5 / 6R) │
                   │  7-term interaction features:  │
                   │  [S_ood, U, D, S*U, S*D, U*D,  │
                   │   S*U*D]                       │
                   └────────────────────────────────┘
                                   │
                                   ▼
                   ┌────────────────────────────────┐
                   │  Unified Reliability Result    │
                   │  - Fused Risk Score R_fused    │
                   │  - Raw OOD, Uncertainty, Drift │
                   └────────────────────────────────┘
```

---

### Workflow B: Explicit Stress Testing Lab

```
Selected Evaluation Data (X_eval)
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Controlled Corruption Generator                        │
│ - Gaussian Noise Stress: X + N(0, severity * std(X))   │
│ - Feature Dropout Stress: zero out fraction = severity │
│ - Feature Permutation Stress: shuffle fraction         │
│ - Combined Stress: sequential noise + dropout + perm    │
│ (OPERATES STRICTLY ON COPIES — NO SOURCE DATA MUTATION)│
└────────────────────────────────────────────────────────┘
          │
          ▼
Stressed Data Matrix (X_stressed)
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Core Reliability Analyzer                              │
│ Computes OOD, Uncertainty, and Drift on X_stressed     │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Fusion Engine Comparison                               │
│ - OriginalFusion vs StressRobustFusion                 │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Stress Reliability Result (StressTestResult)           │
│ - Label-Free: Risk Delta (R_stressed - R_orig)         │
│ - Label-Aware (Optional): Accuracy Delta (Acc_str - Acc)│
└────────────────────────────────────────────────────────┘
```

---

### Workflow C: Explicit Fault Injection Lab & Failure Discovery

```
Selected Evaluation Data (X_eval)
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Structured Fault Injector (Module 7)                   │
│ 1. Feature / Sensor Bias                               │
│ 2. Gain Error                                          │
│ 3. Stuck-At                                            │
│ 4. Channel Swap                                        │
│ 5. Sign Inversion                                      │
│ (OPERATES STRICTLY ON COPIES — NO SOURCE DATA MUTATION)│
└────────────────────────────────────────────────────────┘
          │
          ▼
Faulted Data Copy (X_faulted)
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Core Reliability Analyzer + Fusion Engine              │
│ Computes S_ood, U, D, and Fused Risk Score R_fused     │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Failure Discovery Engine                               │
│ - High-Risk Warning: R_fused >= T_risk                 │
│ - Label-Free Mode: Reports risk changes & warnings     │
│ - Label-Aware Mode (if y_true available):              │
│   • Model Failure: predict(X_faulted) != y_true        │
│   • Confirmed Silent Failure: Failure == 1 & Risk < T  │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Failure Discovery Result (FailureDiscoveryResult)      │
│ Summary by fault family, failure events log            │
└────────────────────────────────────────────────────────┘
```

---

### Workflow D: Failure Memory Flow (Module 8R)

```
Failure / Reliability Events
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Condition Profile Aggregation                          │
│ Aggregates by condition profile:                       │
│ [mean_ood, mean_unc, mean_drift, mean_fused,           │
│  failure_rate, silent_failure_rate]                    │
│ (FAULT LABELS EXCLUDED FROM CLUSTERING INPUTS)         │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Pre-Fitted StandardScaler + KMeans (K=3)               │
│ Fits cluster centroids & 95th percentile thresholds    │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Failure Memory Artifacts                               │
│ Saved to storage/artifacts/                            │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Failure Memory Matcher (FailureMemoryMatcher)          │
│ Incoming Query Profile -> Apply Pre-Fitted Scaler ->   │
│ Argmin Centroid Distance -> Threshold Check -> Match   │
│ (STRICT FIT VS QUERY SEPARATION — NO RE-FITTING)       │
└────────────────────────────────────────────────────────┘
```

---

### Workflow E: Failure Prediction Flow (Module 9R)

```
Historical / Incoming Reliability States
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Prediction Feature Builder                             │
│ Builds Static, Dynamic (deltas Δf_t = f_t - f_{t-1}),   │
│ and Signature-Aware feature matrices                   │
│ (STRICT BACKWARD-LOOKING SAFETY — NO FUTURE LEAKAGE)   │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Failure Predictor (FailurePredictor)                   │
│ Pre-Fitted StandardScaler + RandomForestClassifier     │
│ Predicts P(Upcoming Failure Onset)                     │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Validation-Selected Threshold (ValidationThresholdSelector)│
│ Pre-fixed threshold T_warn selected on Validation split │
│ (TEST SET LABELS CANNOT ALTER PRE-FIXED THRESHOLD)     │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Failure Prediction Result (FailurePredictionResult)    │
│ Predicts next-step onset probability and warning flag  │
└────────────────────────────────────────────────────────┘
```

---

### Workflow F: Temporal Early Warning Flow (Module 10)

```
Ordered Reliability States
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Backward-Looking Temporal Features                     │
│ Dynamic Multi-Signal: [ood, unc, drift, fused, deltas] │
│ (EXCLUDES SEVERITY & FUTURE LABELS)                    │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Warning Model / Dynamic Multi-Signal                   │
│ Pre-Fitted StandardScaler + RandomForestClassifier     │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Validation-Selected Threshold (T_warn ≈ 0.46)          │
│ Selected on Validation split under false warning cap   │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Warning Event (WarningResult / EarlyWarningEvaluation) │
│ State Warning Probability + Trajectory Lead Evaluation │
│ (LEAD TIME UNIT: controlled_degradation_states)        │
└────────────────────────────────────────────────────────┘
```

---

### Workflow G: Research Validation Layer (Modules 11, 12, 13)

```
Real Tabular Research Fixtures & Ablation Sets
(Breast Cancer Wisconsin & Digits Parity)
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Multi-Seed Evaluation Protocol (MultiSeedEvaluator)   │
│ 10 Random Seeds x 2 Domains = 20 Independent Runs      │
│ (ISOLATED RUN STATE & SEVERITY EXCLUDED FROM FEATURES) │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Bootstrap Confidence Intervals (bootstrap_mean_ci)     │
│ 95% Percentile Non-Parametric Bootstrap CIs            │
│ - Mean Fusion AUROC: 0.7849 [0.7589, 0.8117]           │
│ - Mean Spearman: 0.5768 [0.5128, 0.6368]               │
│ - Mean Unseen AUROC: 0.7524 [0.7231, 0.7814]           │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Paired Fusion Hypothesis Evaluation                    │
│ Paired AUPR Gain = AUPR_fusion - AUPR_best_individual  │
│ - Mean Paired Gain: +0.0006                            │
│ - 95% Bootstrap CI: [-0.0082, +0.0084] (INCLUDES ZERO) │
│ - Fusion Win Rate: 70.0% (14/20 wins)                  │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│ Final Research Validation Summary                      │
│ Verdict: ROBUST FRAMEWORK / MIXED FUSION EVIDENCE      │
│ is_fusion_superiority_established = False              │
└────────────────────────────────────────────────────────┘
```

---

## 2. Research & Evaluation Utilities

> **NORMAL MONITORING vs RESEARCH EVALUATION**:
> Normal operational monitoring (`CoreReliabilityAnalyzer.analyze(X)`) evaluates live operational data without refitting components or requiring ground-truth labels.
> Research evaluation routines (`AblationEvaluator`, `CrossDomainEvaluator`, `MultiSeedEvaluator`) live strictly under `aegis/evaluation/` to benchmark system behavior across ablated feature sets, external tabular domains, and multi-seed statistical trials under fair held-out protocols.

---

## 3. Scientific Limitations & Final Defensible Claim

> **FINAL SCIENTIFIC DEFENSIBLE CLAIM**:
> AEGIS-X is a model-agnostic reliability-analysis framework that integrates complementary reliability signals across monitoring, stress testing, failure discovery, characterization, prediction, and warning. Experiments demonstrate reproducible failure-ranking and unseen-fault generalization across controlled and real-data domains, while showing that the predictive advantage of signal fusion over the strongest individual reliability indicator is domain-dependent.
> 
> 1. **Distribution Drift Detection $\neq$ Concept Drift Detection**: Label-free distribution drift measures $P(X)$ shift. Concept drift $P(Y \mid X)$ may occur without large $P(X)$ shift.
> 2. **Signal Visibility**: Operational fusion results MUST NOT hide individual OOD, Uncertainty, and Drift signals. Individual signals must remain separately inspectable.
> 3. **Controlled Experimental Corruptions**: Structured fault injection is a synthetic experimental lab. It does NOT prove an injected feature corruption is a real-world causal hardware root cause.
> 4. **No Causal Root Cause Claims**: Failure signatures represent recurring empirical reliability condition profiles and MUST NOT be interpreted as proven causal root causes.
> 5. **Deployment Evidence Requirement**: Failure prediction capability depends on deployment-specific evidence and MUST NOT be interpreted as universal time-to-failure prediction. Controlled step horizon represents synthetic degradation steps, NOT real-world clock time.
> 6. **Early Warning Horizons Are Controlled Degradation States**: Warning horizons are validated in `controlled_degradation_states`, NOT universal real-world clock time. Historical trajectory-level warning coverage was promising (100%), but the held-out non-failing sample was extremely limited and produced a false warning (100% false warning rate on 1 out of 1 non-failing sample).
> 7. **Cross-Domain Generalization & Statistical Evidence**: Module 12 and Module 13 validate framework behavior across two real tabular research domains (Breast Cancer Wisconsin and Digits Parity) across 20 independent seed runs. While cross-domain failure ranking was strong (mean AUROC $\approx 0.7849$), the 95% bootstrap confidence interval for paired AUPR gain includes zero ($[-0.0082, +0.0084]$), demonstrating that fusion superiority over the strongest individual signal is **statistically inconclusive** and domain-dependent.
