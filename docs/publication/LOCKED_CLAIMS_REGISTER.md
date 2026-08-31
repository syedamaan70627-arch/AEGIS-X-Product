# AEGIS-X Final Locked Scientific Claims Register (Phase G)

| Claim                                                   | Classification     | Evidence                                                                     |
|:--------------------------------------------------------|:-------------------|:-----------------------------------------------------------------------------|
| AEGIS-X detects Far-OOD tabular samples                 | STRONGLY SUPPORTED | AUROC = 0.9994 ± 0.0011 across 5 seeds                                       |
| AEGIS-X detects Near-OOD tabular samples                | SUPPORTED          | AUROC = 0.7333 ± 0.0129 across 5 seeds                                       |
| AEGIS-X estimates prediction uncertainty                | SUPPORTED          | ECE = 0.0806, Brier = 0.0925                                                 |
| Multi-signal fusion improves failure discrimination     | STRONGLY SUPPORTED | Paired Bootstrap p = 1.00e-04 (95% CI: [+0.0206, +0.0510])                   |
| Temporal Failure Prediction provides onset warnings     | SUPPORTED          | Group-split AUROC = 0.9175, F1 = 0.8912                                      |
| Early Warning operates in controlled_degradation_states | SUPPORTED          | Mean lead = 2.79 states                                                      |
| AEGIS-X provides model-interface-agnostic architecture  | STRONGLY SUPPORTED | Evaluated across RandomForest, LogisticRegression, GradientBoosting, and MLP |
| AEGIS-X provides real-world root cause diagnosis        | NOT SUPPORTED      | Explicitly rejected; signature matching is non-causal association            |