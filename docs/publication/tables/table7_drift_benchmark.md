# Table 7: Quantitative Feature Drift Detection Benchmark

| Drift Type              |   Magnitude | Detector      |   True Det Rate |   False Alarm |   Missed Rate | Delay   |
|:------------------------|------------:|:--------------|----------------:|--------------:|--------------:|:--------|
| Sudden Covariate Shift  |         1.5 | KS-Test / PSI |            1    |          0    |          0    | 0 steps |
| Gradual Covariate Drift |         0.5 | ADWIN / PSI   |            0.95 |          0.02 |          0.05 | 2 steps |
| Recurring Shift         |         1.2 | KS-Test       |            0.98 |          0.01 |          0.02 | 0 steps |