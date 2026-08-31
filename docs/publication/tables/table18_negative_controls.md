# Table 18: Negative-Control & Sanity Experiments Leakage Audit

| Sanity Experiment                     | Expected Behavior                          |   Observed AUROC | Leakage Audit                           |
|:--------------------------------------|:-------------------------------------------|-----------------:|:----------------------------------------|
| 1. Target-Label Permutation Control   | AUROC collapses to ~0.50                   |           0.5012 | PASSED (No Target Leakage)              |
| 2. Random Reliability-Signal Control  | AUROC collapses to ~0.50                   |           0.4985 | PASSED (No Signal Spuriousness)         |
| 3. Randomized Temporal Sequence Order | Lag Model AUROC drops > 0.35               |           0.521  | PASSED (Strict Temporal Order Required) |
| 4. Sequence-ID Leakage Audit          | Zero predictive power from ID alone        |           0.5    | PASSED (Group Split Verified)           |
| 5. Removal of Target-Derived Features | Valid predictors use lag features only     |           0.9175 | PASSED (Valid Feature Set)              |
| 6. Feature-Shuffle Sensitivity Test   | AUC drops monotonically with shuffle ratio |           0.542  | PASSED (Feature Sensitivity Verified)   |