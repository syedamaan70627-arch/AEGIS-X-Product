# AEGIS-X Integration Contract & Specification

**Version:** 1.0 (Phase A — Integration Layer)  
**Status:** Active Core Contract  

---

## 1. Introduction & Overview

AEGIS-X is a research-backed, model-agnostic AI reliability framework designed to surround existing trained machine learning models. Rather than replacing or retraining your model, AEGIS-X monitors, stresses, and predicts failure conditions by analyzing feature distributions, prediction uncertainties, and operational shifts.

This document defines the formal **Integration Contract** required to connect an existing trained model and dataset to AEGIS-X for reliability analysis.

---

## 2. Input Requirements

### 2.1 Model Requirements
AEGIS-X accepts trained scikit-learn compatible classification models:
* **Serialization Formats:** `.joblib` or `.pkl` (pickle) files.
* **Required Interface:** Must implement a callable `predict(X)` method accepting tabular feature matrices (DataFrame or NumPy array).
* **Preferred Interface:** `predict_proba(X)` returning probability matrices. When present, probability scores enable advanced confidence-based uncertainty analysis.
* **Supported Task Types:**
  * `BINARY_CLASSIFICATION`
  * `MULTICLASS_CLASSIFICATION`

> [!WARNING]  
> **Security Notice:** Loading `.joblib` or `.pkl` files involves Python object deserialization, which can execute arbitrary code. Only register model files that originate from trusted internal storage or verified build pipelines.

---

### 2.2 Reference Dataset Requirements
The **Reference Dataset** represents the baseline operating distribution under which the model was trained or validated.
* **File Format:** Comma-Separated Values (CSV).
* **Feature Schema:** Must match the exact numerical feature space expected by the model.
* **Target Labels:** Optional. True ground-truth labels can be included for retrospective accuracy checks, but are not required for core operational reliability analysis.

---

### 2.3 Evaluation Dataset Requirements
The **Evaluation Dataset** represents the current or new operational data snapshot being assessed for reliability risks.
* **File Format:** Comma-Separated Values (CSV).
* **Feature Schema:** Must contain the same feature columns as the Reference Dataset. Columns will be automatically re-aligned if names match but order differs.
* **Target Labels:** Optional.

---

## 3. Reference vs. Evaluation Datasets

| Parameter | Reference Dataset | Evaluation Dataset |
| :--- | :--- | :--- |
| **Role** | Baseline distribution (known safe operating state) | Target data stream (current operational state) |
| **Origin** | Training data subset or validation benchmark | Real-world production telemetry or test batches |
| **Purpose** | Establishes density, feature ranges, and uncertainty baselines | Evaluated for OOD shifts, drift, and reliability degradation |
| **Ground Truth Labels** | Optional | Optional |

---

## 4. Label-Free Operational Reliability

A key architectural design principle of AEGIS-X is **Label-Free Operational Monitoring**:

> In real-world production environments, ground-truth target labels ($y$) are often delayed, expensive, or completely unavailable at inference time.

AEGIS-X performs the following core reliability analyses **without requiring ground-truth labels**:
1. **Out-of-Distribution (OOD) Detection:** Identifies samples lying outside the reference feature space density.
2. **Predictive Uncertainty Estimation:** Measures model decision confidence and entropy from feature space representations and prediction probabilities.
3. **Feature & Covariate Drift Analysis:** Measures statistical divergence (e.g., Wasserstein distance, Kolmogorov-Smirnov tests) between reference and evaluation feature distributions ($P(X_{eval}) \neq P(X_{ref})$).

**When True Labels Are Provided:** Ground-truth labels are utilized for retrospective performance diagnostic metrics (e.g., confusion matrix shifts, calibrated accuracy loss).

---

## 5. Version 1 Limitations

For Version 1 (Phase A foundation), the following scope boundaries apply:

1. **Model Scope:** Tabular classification models serialized via `joblib` or `pickle` only.
2. **Feature Types:** Strictly numerical feature columns in CSV format (categorical features must be pre-encoded prior to integration).
3. **Unsupported Formats (Planned for Future Releases):**
   * REST prediction API endpoints
   * Direct prediction log CSV files (without model binary)
   * Deep learning frameworks (PyTorch, TensorFlow / Keras)
   * Image, audio, or unstructured text data streams

---

## 6. Integration Workflow Summary

```
User Model (.joblib / .pkl)
            +
Reference Dataset (CSV)
            +
Evaluation Dataset (CSV)
            │
            ▼
 ┌──────────────────────┐
 │ IntegrationValidator │
 └──────────┬───────────┘
            │  (Validates feature schema, predict interface, and shapes)
            ▼
    ValidatedInput Container
            │
            ▼
 AEGIS-X Reliability Engine
```
