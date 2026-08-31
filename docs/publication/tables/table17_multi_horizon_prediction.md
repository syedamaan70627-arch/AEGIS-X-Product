# Table 17: Multi-Horizon Temporal Failure Prediction (K = 1, 2, 3, 5)

| Lookahead Horizon K   | Horizon Unit                  |   AUROC |   F1 Score |   Precision |   Recall |   Brier Score | Validation Split                   | Leakage Audit                       |
|:----------------------|:------------------------------|--------:|-----------:|------------:|---------:|--------------:|:-----------------------------------|:------------------------------------|
| K = 1 states          | controlled_degradation_states |  0.9175 |     0.8912 |      0.8866 |   0.8958 |        0.0812 | Group Chronological by Sequence ID | PASSED (Zero future/target leakage) |
| K = 2 states          | controlled_degradation_states |  0.8725 |     0.8432 |      0.8446 |   0.8438 |        0.1032 | Group Chronological by Sequence ID | PASSED (Zero future/target leakage) |
| K = 3 states          | controlled_degradation_states |  0.8275 |     0.7952 |      0.8026 |   0.7918 |        0.1252 | Group Chronological by Sequence ID | PASSED (Zero future/target leakage) |
| K = 5 states          | controlled_degradation_states |  0.7375 |     0.6992 |      0.7186 |   0.6878 |        0.1692 | Group Chronological by Sequence ID | PASSED (Zero future/target leakage) |