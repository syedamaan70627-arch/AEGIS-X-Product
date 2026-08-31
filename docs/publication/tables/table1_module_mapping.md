# Table 1: AEGIS-X Research Module Operational & Scientific Validation Mapping

| Module                 | Method                               | Status      | Metric                        |
|:-----------------------|:-------------------------------------|:------------|:------------------------------|
| OOD Detection          | Mahalanobis / KNN Distance           | OPERATIONAL | AUROC, AUPR, FPR@95           |
| Uncertainty Estimation | Calibrated Entropy / Variance        | OPERATIONAL | NLL, Brier, ECE               |
| Drift Detection        | PSI, KS, Chi-Square, ADWIN           | OPERATIONAL | p-value, Drift Flags          |
| Signal Fusion          | StressRobust Fusion Engine           | OPERATIONAL | Fused Risk Score              |
| Stress Testing         | Controlled Perturbation / Noise      | OPERATIONAL | Risk Delta, Severity Curve    |
| Fault Injection        | 5-Type Fault Taxonomy                | OPERATIONAL | Silent Failure Rate           |
| Failure Explorer       | Retrospective Label-Aware Diagnostic | OPERATIONAL | Failure Event Counts          |
| Failure Memory         | K-Means Signature Centroids          | OPERATIONAL | Silhouette, Distance          |
| Failure Prediction     | Temporal Lagged RandomForest/GB      | OPERATIONAL | AUROC, F1, Brier              |
| Early Warning          | Multi-Signal Lead Evaluation         | OPERATIONAL | controlled_degradation_states |
| Reporting              | Executive & Export Engine            | OPERATIONAL | JSON, CSV, Print View         |