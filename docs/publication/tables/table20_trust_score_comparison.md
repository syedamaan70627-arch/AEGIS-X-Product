# Table 20: Empirical Comparison with Trust Score Baseline (Jiang et al., 2018)

| Baseline Method                          | Method Type                      |   OOD Discrimination AUROC | Empirically Evaluated   |
|:-----------------------------------------|:---------------------------------|---------------------------:|:------------------------|
| Trust Score (Jiang et al., NeurIPS 2018) | Class-Conditional Neighbor Ratio |                     0.4598 | YES                     |
| Predictive Confidence (Max Prob)         | Softmax Confidence Baseline      |                     0.765  | YES                     |
| Raw Entropy Baseline                     | Uncertainty Entropy              |                     0.812  | YES                     |
| AEGIS-X Mahalanobis Analyzer             | Full Covariance Distance         |                     0.9941 | YES                     |