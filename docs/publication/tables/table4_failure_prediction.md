# Table 4: Failure Prediction Feature Ablation & 95% Confidence Intervals

| Predictor Feature Subset                       |   AUROC | 95% CI           |   F1 Score |   Brier |
|:-----------------------------------------------|--------:|:-----------------|-----------:|--------:|
| Full Reliability History (OOD+Unc+Drift+Fused) |  0.9175 | [0.8950, 0.9400] |     0.8912 |  0.0812 |
| Full minus OOD History                         |  0.841  | [0.8120, 0.8700] |     0.81   |  0.124  |
| Full minus Uncertainty History                 |  0.885  | [0.8600, 0.9100] |     0.852  |  0.098  |
| Full minus Drift History                       |  0.892  | [0.8680, 0.9160] |     0.864  |  0.093  |
| Fused Risk History Only                        |  0.889  | [0.8630, 0.9150] |     0.859  |  0.095  |