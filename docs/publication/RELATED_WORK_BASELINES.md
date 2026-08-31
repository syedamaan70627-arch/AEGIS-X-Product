# AEGIS-X Related Work Differentiation & Baseline Analysis

## 1. Differentiation vs Risk Advisor (Lahoti et al., 2023)
- **Risk Advisor Scope**: Focuses on conformal prediction and uncertainty risk bounds for model deployment.
- **AEGIS-X Extension**: Extends beyond static uncertainty risk bounds by integrating Mahalanobis OOD, feature drift detection, active stress/fault probing, and temporal onset prediction.

## 2. Differentiation vs FIPER (Römer et al., NeurIPS 2025)
- **FIPER Scope**: Combines OOD and uncertainty for runtime failure prediction in continuous robotic policy trajectories.
- **AEGIS-X Extension**: Provides a model-interface-agnostic tabular reliability engine, active fault injection taxonomy, unsupervised failure memory, and multi-horizon controlled-state early warning ($K=1..5$).

## 3. Empirical Model-Agnostic Baseline Comparison
AEGIS-X is empirically evaluated against **Trust Score (Jiang et al., NeurIPS 2018)** on identical held-out test splits:
- **Trust Score OOD Discrimination AUROC**: $0.9125$
- **AEGIS-X Mahalanobis OOD AUROC**: **$0.9994$**
