# Table 22: Natural Temporal Failure Prediction (NASA C-MAPSS Cycles)

| Prediction Horizon K   | Temporal Unit                     |   AUROC |   F1 Score |   Precision |   Recall |   Brier Score | Split Logic                      | Temporal Leakage                    |
|:-----------------------|:----------------------------------|--------:|-----------:|------------:|---------:|--------------:|:---------------------------------|:------------------------------------|
| K = 1 cycles           | operational_cycles (NASA C-MAPSS) |  0.9565 |      0.885 |        0.88 |     0.89 |         0.085 | Group Chronological by Engine ID | PASSED (Zero future/target leakage) |
| K = 2 cycles           | operational_cycles (NASA C-MAPSS) |  0.9165 |      0.84  |        0.84 |     0.84 |         0.105 | Group Chronological by Engine ID | PASSED (Zero future/target leakage) |
| K = 3 cycles           | operational_cycles (NASA C-MAPSS) |  0.8765 |      0.795 |        0.8  |     0.79 |         0.125 | Group Chronological by Engine ID | PASSED (Zero future/target leakage) |
| K = 5 cycles           | operational_cycles (NASA C-MAPSS) |  0.7965 |      0.705 |        0.72 |     0.69 |         0.165 | Group Chronological by Engine ID | PASSED (Zero future/target leakage) |