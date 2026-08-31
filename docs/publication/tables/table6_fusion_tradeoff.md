# Table 6: Original vs StressRobust Fusion Trade-Off Evaluation

|   Noise Severity |   Original Fused Risk |   StressRobust Fused Risk |   Risk Bounds Variance Delta | Robustness Advantage            |
|-----------------:|----------------------:|--------------------------:|-----------------------------:|:--------------------------------|
|              0   |                0.3286 |                    0.545  |                       0.2163 | Equivalent baseline             |
|              0.2 |                0.426  |                    0.6181 |                       0.1921 | Equivalent baseline             |
|              0.5 |                0.6846 |                    0.7255 |                       0.0409 | Dampens extreme variance spikes |
|              0.8 |                0.809  |                    0.7874 |                       0.0216 | Dampens extreme variance spikes |
|              1   |                0.85   |                    0.8124 |                       0.0376 | Dampens extreme variance spikes |