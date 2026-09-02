# AEGIS-X V1 Frozen Reference Baseline

**Freeze Date**: September 2, 2026  
**Commit Hash**: `0f7b48fa43e2c4a07d5acb05bbef06703c83c810`  
**Repository Branch**: `main` (`origin/main`)  
**Status**: Frozen & Immutable Baseline  

---

## 1. Executive Immutability Statement

> [!IMPORTANT]
> **IMMUTABILITY CONTRACT**: AEGIS-X Modules 1–13, their underlying scientific algorithms (`StressRobustFusion`, `controlled_degradation_states`), stored dataset records, benchmark metrics, and security RLS policies are **frozen reference baselines**.
> Module 14 — Evidence-Calibrated Reliability Governance (ECRG) operates strictly as an additive, non-destructive decision-calibration layer. Module 14 will **never** retrain, overwrite, modify, or redeploy a monitored user model or historical benchmark artifact.

---

## 2. Inventory of Frozen Modules (Modules 1–13)

| Module | Title | Core Algorithm / Functionality | Output Signals / Metrics |
| :--- | :--- | :--- | :--- |
| **Module 1** | Pre-label OOD Detection | Isolation Forest / Mahalanobis Distance | `ood_score` $\in [0, 1]$ |
| **Module 2** | Uncertainty Quantifier | Entropy & Variance Estimation | `uncertainty_score` $\in [0, 1]$ |
| **Module 3** | Feature Drift Detector | Kolmogorov-Smirnov & Wasserstein Distance | `drift_score` $\in [0, 1]$ |
| **Module 4** | Pre-label Risk Fusion | `StressRobustFusion` (Adversarial Robustness) | `aggregate_fused_risk` $\in [0, 1]$ |
| **Module 5** | Stress Testing Lab | Synthetic Noise / Outlier / Covariate Injection | Stress Robustness Curve |
| **Module 6** | Fault Injection Engine | Stuck-at / Sensor Bias / Noise Corruption | Fault Sensitivity Profile |
| **Module 7** | Failure Signature Explorer | Unsupervised Cluster & Anomaly Masking | Signature Vector & Cluster Id |
| **Module 8** | Retrospective Evaluator | Diagnostic Accuracy & Spearman Correlation | Accuracy, Error Rate, Spearman $\rho$ |
| **Module 9** | Publication Benchmark | C-MAPSS FD001–FD004 & Synthetic Suite | AUROC, AUPRC, Lead Time |
| **Module 10** | Enterprise Platform | FastAPI Backend & Centralized Typed API Client | REST API / Bearer Auth |
| **Module 11** | Failure Memory Bank | Associative k-NN & Cosine Similarity Matcher | `memory_similarity` $\in [0, 1]$ |
| **Module 12** | Temporal Predictor | Sequence Hazard & Multi-step Horizon Model | `temporal_failure_probability` |
| **Module 13** | Early Warning Unit | `controlled_degradation_states` Lead Unit | Degradation Lead ($K \in \{1, 2, 3, 5\}$) |

---

## 3. Reference Production Resources & Identifiers

- **Production Model ID**: `013245af-9a9a-4e59-9648-0bb135f604d7` (`AEGIS Test RF`, Binary Classification, 10 Features)
- **Reference Analysis ID**: `3fabcdd7-de58-4d36-87c5-34674e8c0d0b`
- **Reference Datasets**:
  - `reference_dataset.csv`
  - `evaluation_dataset.csv`
  - `sample_temporal_trajectory.csv`
- **Evaluation Seeds**: `42`, `100`, `2026`

---

## 4. Current System Architecture & Security Posture

1. **Frontend Architecture**: Next.js 16.3.3 App Router, TypeScript, Vanilla CSS (Enterprise Slate palette), Tailwind CSS.
2. **Backend Engine**: FastAPI REST API (`api/main.py`), Pydantic V2 schemas, PyTorch / Scikit-Learn signal execution engine.
3. **Database & Auth**: Supabase PostgreSQL with Row-Level Security (RLS) enabled across all tables; Bearer JWT token verification on all protected endpoints (`/api/v1/*`).
4. **Deployment Scopes**:
   - Production API: `https://aegis-x-product-production.up.railway.app/api/v1`
   - Frontend: Vercel fail-closed deployment scope.

---

## 5. Frozen Limitations & Negative Findings

1. Pre-label detectors operate without ground-truth outcome labels; high fused risk indicates signal divergence or distribution shift, not guaranteed prediction error.
2. Associative failure memory accuracy is strictly bounded by the diversity of previously ingested failure signatures.
3. Temporal prediction and early warning lead estimation require sequential time-series input with consistent sampling frequency.
4. `StressRobustFusion` weights remain fixed post-calibration to maintain deterministic signal output.
