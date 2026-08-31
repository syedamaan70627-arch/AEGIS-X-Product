# IEEE Conference / Journal Scientific Evidence Package for AEGIS-X

**System Title**: AEGIS-X: A Model-Interface-Agnostic Engine for AI Reliability, Stress Testing, Failure Memory, and Temporal Onset Prediction  
**Status**: INDEPENDENTLY VERIFIED & REPRODUCIBLE  
**Verification Date**: 2026-08-31  

---

## Executive Evidence Summary

AEGIS-X has undergone rigorous Phase F independent scientific verification across 5 random seeds (42, 43, 44, 45, 46) and 4 distinct model families (RandomForest, LogisticRegression, GradientBoosting, MLPClassifier). All experimental claims have been audited for leakage, target contamination, and reproducibility.

### Key Verified Metrics

1. **Far-OOD Detection**: AUROC = **0.9994 ± 0.0011**, FPR@95 = **0.0000**
2. **Near-OOD Detection**: AUROC = **0.7333 ± 0.0129**
3. **Uncertainty Calibration**: ECE = **0.0806**, Brier Score = **0.0925**
4. **Signal Fusion Discrimination**: AUROC = **0.9895** (Paired Bootstrap $p < 0.001$, 95% CI: [+0.0206, +0.0510])
5. **Temporal Failure Prediction**: AUROC = **0.9175**, F1 Score = **0.8912** (Leakage-free Group Split)
6. **Early Warning Lead Horizon**: Mean = **2.79** `controlled_degradation_states`

---

## Complete Publication Tables Manifest

- `docs/publication/tables/table1_module_mapping.md`: Research Module Mapping
- `docs/publication/tables/table2_ood_validation.md`: OOD Performance Breakdown
- `docs/publication/tables/table3_uncertainty_calibration.md`: Calibration Metrics
- `docs/publication/tables/table4_failure_prediction.md`: Temporal Prediction & Leakage Audit
- `docs/publication/tables/table5_ablation_study.md`: 13-Variant Signal Ablation
- `docs/publication/tables/table7_drift_benchmark.md`: Feature Drift Detection Metrics
- `docs/publication/tables/table8_failure_memory_evaluation.md`: Unsupervised Signature Clustering
- `docs/publication/tables/table10_early_warning_evaluation.md`: Lead Horizon Distribution
- `docs/publication/tables/table11_statistical_bootstrapping.md`: 1,000-Resample Bootstrap Significance
- `docs/publication/tables/table12_model_family_breakdown.md`: 4-Model Family Generalization
- `docs/publication/tables/table13_multi_seed_reproducibility.md`: Multi-Seed Aggregated Means & CIs

---

## Reproducibility Instructions

To reproduce all tables, figures, and artifacts from scratch:
```bash
python aegis/experiments/run_phase_f_verification.py
```
