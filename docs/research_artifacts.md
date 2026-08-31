# AEGIS-X Research Artifacts Inventory

This document details every fitted object, model binary, dataset, and state file produced or consumed across Modules 1 through 13 of the AEGIS-X research pipeline (`research_source/AEGIS_X_01_Baseline.ipynb`).

---

## Classification Taxonomy

Every research artifact is classified under one of five production readiness categories:

- **A. Fit from the user's reference data**: Must be trained/fitted directly on the user's nominal operational dataset during deployment setup.
- **B. Load as an existing validated artifact**: Can be loaded directly as a pre-trained reference binary or historical benchmark database.
- **C. Fit/configure during AEGIS-X product setup**: Generated during the AEGIS-X automated initialization/calibration setup sequence.
- **D. Research-only evidence and should not be used operationally**: Scientific proof, ablation logs, or superseded experimental models.
- **E. Unclear / requires later decision**: Ambiguous state needing further user/architectural review.

---

## Artifact Inventory List

### 1. `aegis_baseline_model.pkl` / `random_forest.pkl`
- **Research Module**: Module 1 (Baseline Model Setup)
- **Purpose**: Core classification model predicting primary task labels $y$ from feature vector $X$.
- **How Created**: Trained on clean reference feature split using `RandomForestClassifier(n_estimators=100, random_state=42)`.
- **Where It Currently Comes From**: Notebook Cell 19, saved to `models/aegis_baseline_model.pkl`.
- **Regenerate or Preserve**: Regenerate on user's target reference dataset during installation.
- **Required for Product Operation**: Yes.
- **Data/Test Leakage Risk**: Low if trained exclusively on reference training split without test samples.
- **Classification**: **A** (Fit from the user's reference data)

---

### 2. `scaler.pkl`
- **Research Module**: Module 1 (Baseline Model Setup)
- **Purpose**: Normalizes input features ($Z$-score scaling) required for baseline prediction, OOD distance, and uncertainty estimators.
- **How Created**: Fitted using `StandardScaler().fit(X_train)`.
- **Where It Currently Comes From**: Notebook Cell 19, saved to `models/scaler.pkl`.
- **Regenerate or Preserve**: Regenerate on user's target reference dataset.
- **Required for Product Operation**: Yes.
- **Data/Test Leakage Risk**: Low if fitted strictly on training split.
- **Classification**: **A** (Fit from the user's reference data)

---

### 3. `aegis_normal_reference.csv`
- **Research Module**: Module 1 (Baseline Model Setup)
- **Purpose**: Clean baseline feature dataset representing nominal system operation under non-fault conditions.
- **How Created**: Synthesized via multivariate normal generator or loaded from reference CSV stream.
- **Where It Currently Comes From**: Notebook Cell 20, saved to `data/synthetic/aegis_normal_reference.csv`.
- **Regenerate or Preserve**: Provided by user or configured during system setup.
- **Required for Product Operation**: Yes (required to fit OOD, drift reference distributions, and calibrators).
- **Data/Test Leakage Risk**: Critical — must strictly contain nominal operating points without corrupted fault data.
- **Classification**: **A** (Fit from the user's reference data)

---

### 4. `isolation_forest.pkl`
- **Research Module**: Module 2 (Out-of-Distribution Detection)
- **Purpose**: Unsupervised tree ensemble estimating spatial feature out-of-distribution scores.
- **How Created**: Fitted on reference dataset using `IsolationForest(contamination=0.01, random_state=42)`.
- **Where It Currently Comes From**: Notebook Cells 25 & 87, saved to `models/ood/isolation_forest.pkl`.
- **Regenerate or Preserve**: Fit during AEGIS-X setup on reference data.
- **Required for Product Operation**: Yes.
- **Data/Test Leakage Risk**: Low if trained on clean nominal reference split.
- **Classification**: **C** (Fit/configure during AEGIS-X product setup)

---

### 5. `bootstrap_uncertainty_ensemble.pkl`
- **Research Module**: Module 3 (Uncertainty Estimation & Calibration)
- **Purpose**: Ensemble of 10 sub-classifiers trained on bootstrap resamples to quantify prediction variance (epistemic uncertainty).
- **How Created**: Trained 10 sub-classifiers on bootstrapped splits of nominal training dataset.
- **Where It Currently Comes From**: Notebook Cells 48 & 89, saved to `models/uncertainty/bootstrap_uncertainty_ensemble.pkl`.
- **Regenerate or Preserve**: Fit during AEGIS-X setup.
- **Required for Product Operation**: Yes.
- **Data/Test Leakage Risk**: Low if sub-models are trained on bootstraps of reference training data.
- **Classification**: **C** (Fit/configure during AEGIS-X product setup)

---

### 6. `platt_calibrator.pkl`
- **Research Module**: Module 3 (Uncertainty Estimation & Calibration)
- **Purpose**: Logistic regression model mapping uncalibrated model probabilities into well-calibrated confidence scores.
- **How Created**: Fitted using `LogisticRegression` on validation set prediction logits against ground truth labels.
- **Where It Currently Comes From**: Notebook Cells 44 & 59, saved to `models/uncertainty/platt_calibrator.pkl`.
- **Regenerate or Preserve**: Fit during AEGIS-X setup using a dedicated validation split.
- **Required for Product Operation**: Yes.
- **Data/Test Leakage Risk**: High risk if fitted on training data; must use holdout validation split to prevent overconfidence.
- **Classification**: **C** (Fit/configure during AEGIS-X product setup)

---

### 7. `reference_distribution.pkl`
- **Research Module**: Module 4 (Concept Drift Detection Engine)
- **Purpose**: Reference feature distribution quantiles and summary statistics used for Kolmogorov-Smirnov drift tests and ADWIN baselines.
- **How Created**: Computed across reference feature dataset columns.
- **Where It Currently Comes From**: Notebook Cells 64 & 90, saved to `models/drift/reference_distribution.pkl`.
- **Regenerate or Preserve**: Calculate during setup on reference dataset.
- **Required for Product Operation**: Yes.
- **Data/Test Leakage Risk**: None if derived strictly from reference set.
- **Classification**: **C** (Fit/configure during AEGIS-X product setup)

---

### 8. `fusion_linear_model.pkl` & `fusion_interaction_model.pkl`
- **Research Module**: Module 5 (Unified Reliability & Risk Fusion Engine)
- **Purpose**: Naive linear regression fusion model trained in initial Module 5 attempt to combine OOD, uncertainty, and drift scores.
- **How Created**: Trained on unperturbed validation signals.
- **Where It Currently Comes From**: Notebook Cells 102 & 112, saved to `models/fusion/`.
- **Regenerate or Preserve**: Do NOT use operationally; superseded by Module 6R robust fusion model.
- **Required for Product Operation**: No.
- **Data/Test Leakage Risk**: Failed under stress testing (collapsed under signal noise).
- **Classification**: **D** (Research-only evidence and should not be used operationally)

---

### 9. `stress_robust_fusion.pkl`
- **Research Module**: Module 6R (Controlled Stress Testing & Stress-Robust Fusion)
- **Purpose**: Meta-fusion regression/classification model trained to combine OOD distance, epistemic uncertainty, and drift signals reliably under stress.
- **How Created**: Trained on stress-perturbed dataset generated in Module 6R using group-aware splitting.
- **Where It Currently Comes From**: Notebook Cells 131 & 140, saved to `models/fusion/stress_robust_fusion.pkl`.
- **Regenerate or Preserve**: Preserved as default robust fusion weights or retrained during setup.
- **Required for Product Operation**: Yes.
- **Data/Test Leakage Risk**: Requires group-aware splitting (grouping by stress injection run ID) to prevent temporal leakage between stress samples.
- **Classification**: **C** (Fit/configure during AEGIS-X product setup)

---

### 10. `failure_signature_model_refined.pkl` & `failure_signature_scaler_refined.pkl`
- **Research Module**: Module 8R (Failure Signatures & Failure Memory Engine)
- **Purpose**: Clustering model (`KMeans`) and scaler used to match live anomaly feature vectors against historical failure signature centroids.
- **How Created**: Fitted on feature vectors extracted from Module 7 fault injection replicate events.
- **Where It Currently Comes From**: Notebook Cells 187 & 206, saved to `models/failure_memory/`.
- **Regenerate or Preserve**: Can be loaded as pre-trained reference signatures or updated online.
- **Required for Product Operation**: Recommended for failure diagnosis and memory matching.
- **Data/Test Leakage Risk**: Signatures represent associative signal clusters, not causal root causes; validate on holdout fault runs.
- **Classification**: **B** (Load as an existing validated artifact) or **C** (Fit/configure during product setup)

---

### 11. `prediction_meta_selection.csv` & Multi-Horizon Predictors (`_h1.pkl`, `_h3.pkl`, `_h5.pkl`, `_h10.pkl`)
- **Research Module**: Module 9 / 9R (Multi-Horizon Failure Prediction)
- **Purpose**: Predict failure probability $h$ time steps in advance.
- **How Created**: Trained on windowed sequence data of historical risk states.
- **Where It Currently Comes From**: Notebook Cells 204 & 214, saved to `models/failure_prediction/`.
- **Regenerate or Preserve**: Load validated pre-trained predictors or retrain during product setup.
- **Required for Product Operation**: Recommended for predictive early warning capabilities.
- **Data/Test Leakage Risk**: Sliding window construction must preserve temporal causality (no future leakage).
- **Classification**: **B** (Load as an existing validated artifact) / **C** (Fit during setup)

---

### 12. `early_warning_config.json`, `early_warning_model_h3.pkl`, `early_warning_scaler.pkl`
- **Research Module**: Module 10 (Temporal Early Warning)
- **Purpose**: Dynamic Multi-Signal temporal warning engine predicting failure risk over multi-state warning horizons ($H^*=3$ controlled degradation states).
- **How Created**: Trained on windowed temporal state sequences using validation-only threshold selection under false warning constraints ($\le 0.20$).
- **Where It Currently Comes From**: Notebook Cells 215–220, saved to `models/early_warning/`.
- **Regenerate or Preserve**: Load pre-trained warning artifacts or configure during deployment setup.
- **Required for Product Operation**: Recommended for multi-state early warning and lead evaluation.
- **Data/Test Leakage Risk**: Horizon units represent controlled degradation states, NOT clock time. Validation-only threshold selection must be preserved.
- **Classification**: **B** (Load as an existing validated artifact) / **C** (Fit during setup)

---

### 13. Research Experimental Results Datasets (`*.csv`)
- **Research Module**: Modules 1 – 13
- **Artifact Names**:
  - `validation_model_comparison.csv` (Module 1)
  - `ood_validation_results.csv`, `ood_test_signals.csv`, `ood_detector_comparison.csv` (Module 2)
  - `uncertainty_test_signals.csv`, `calibration_comparison.csv` (Module 3)
  - `drift_window_signals.csv`, `adwin_results.csv`, `normal_drift_calibration.csv` (Module 4)
  - `aegis_unified_risk_signals.csv`, `weighted_fusion_search.csv`, `bootstrap_fusion_comparison.csv` (Module 5)
  - `controlled_stress_results_robust.csv`, `stress_risk_failure_correlations_robust.csv` (Module 6R)
  - `all_fault_events.csv`, `fault_component_responses.csv`, `fault_replicate_results.csv`, `silent_failure_conditions.csv` (Module 7)
  - `failure_signature_profiles.csv`, `failure_memory_holdout_validation.csv`, `fault_memory_coverage.csv` (Module 8R)
  - `prediction_final_results.csv`, `pre_failure_onset_predictions.csv` (Module 9R)
  - `trajectory_lead_time_results.csv`, `early_warning_validation.csv`, `early_warning_final_results.csv` (Module 10)
  - `component_removal_effects.csv`, `trajectory_ablation_results.csv` (Module 11)
  - `cross_domain_boundaries.csv` (Module 12)
  - `multi_seed_domain_aggregate.csv` (Module 13)
- **Purpose**: Static experimental evidence, benchmarks, and statistical evaluation tables.
- **How Created**: Generated during full notebook execution.
- **Where It Currently Comes From**: Notebook results directories.
- **Regenerate or Preserve**: Preserve as static scientific proof documentation.
- **Required for Product Operation**: No.
- **Data/Test Leakage Risk**: N/A.
- **Classification**: **D** (Research-only evidence and should not be used operationally)

---

## Summary of Artifact Classifications

| Classification Category | Count | Primary Artifacts |
| :--- | :---: | :--- |
| **A. Fit from user's reference data** | 3 | `aegis_baseline_model.pkl`, `scaler.pkl`, `aegis_normal_reference.csv` |
| **B. Load as existing validated artifact** | 3 | `failure_signature_profiles.csv`, `prediction_meta_selection.csv`, `early_warning_config.json` |
| **C. Fit/configure during AEGIS-X setup** | 7 | `isolation_forest.pkl`, `bootstrap_uncertainty_ensemble.pkl`, `platt_calibrator.pkl`, `reference_distribution.pkl`, `stress_robust_fusion.pkl`, `failure_signature_model_refined.pkl`, `early_warning_model_h3.pkl` |
| **D. Research-only evidence** | 15+ | Initial naive linear fusion models (`fusion_linear_model.pkl`), experimental CSV evaluation tables across Modules 1–13 |
| **E. Unclear / requires later decision** | 0 | None. All artifacts are fully categorized. |
