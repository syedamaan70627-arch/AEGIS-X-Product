# AEGIS-X Re-Audited Scientific Claims Register (Phase F)

| Claim                                                     | Classification   | Evidence                                                                     |
|:----------------------------------------------------------|:-----------------|:-----------------------------------------------------------------------------|
| AEGIS-X detects Far-OOD tabular samples                   | SUPPORTED        | AUROC=0.9994 ± 0.0011                                                        |
| AEGIS-X detects Near-OOD tabular samples                  | SUPPORTED        | AUROC=0.7333 ± 0.0129                                                        |
| AEGIS-X estimates prediction uncertainty                  | SUPPORTED        | Calibrated ECE=0.0806, Brier=0.0925                                          |
| Multi-signal fusion improves failure discrimination       | SUPPORTED        | Bootstrap paired diff p=1.0000e-04 (95% CI: [+0.0206, +0.0510])              |
| Temporal Failure Prediction provides onset warnings       | SUPPORTED        | Leakage-free group split AUROC=0.9175                                        |
| Early Warning lead horizon operates in degradation states | SUPPORTED        | Mean lead = 2.79 controlled_degradation_states                               |
| AEGIS-X is model-interface-agnostic                       | SUPPORTED        | Evaluated across RandomForest, LogisticRegression, GradientBoosting, and MLP |
| AEGIS-X provides real-world root cause diagnosis          | NOT_SUPPORTED    | Explicitly rejected; signature matching is non-causal association            |