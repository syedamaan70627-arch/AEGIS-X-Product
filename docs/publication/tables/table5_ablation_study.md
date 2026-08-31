# Table 5: Comprehensive 13-Variant AEGIS-X Ablation Study

| Variant / Signal Combination   |   AUROC |   AUPRC |   F1 Score |   Precision |   Recall |   Brier Score |
|:-------------------------------|--------:|--------:|-----------:|------------:|---------:|--------------:|
| Full AEGIS-X (StressRobust)    |  0.9902 |  0.9949 |     0.7578 |      0.61   |   1      |        0.2062 |
| Full AEGIS-X (Original)        |  0.9823 |  0.9899 |     0.9042 |      0.9902 |   0.832  |        0.1875 |
| Full minus OOD                 |  0.866  |  0.9183 |     0.2937 |      1      |   0.1721 |        0.2614 |
| Full minus Uncertainty         |  0.9244 |  0.9539 |     0.5896 |      1      |   0.418  |        0.2086 |
| Full minus Drift               |  0.9842 |  0.9909 |     0.8    |      0.6667 |   1      |        0.1806 |
| Full minus Failure Memory      |  0.9902 |  0.9949 |     0.7578 |      0.61   |   1      |        0.2062 |
| OOD Only                       |  0.956  |  0.9735 |     0.7967 |      0.6639 |   0.9959 |        0.1615 |
| Uncertainty Only               |  0.8257 |  0.8816 |     0.814  |      0.7117 |   0.9508 |        0.2143 |
| Drift Only                     |  0.7621 |  0.8698 |     0.2817 |      1      |   0.1639 |        0.4036 |
| OOD + Uncertainty              |  0.9842 |  0.9909 |     0.8    |      0.6667 |   1      |        0.1806 |
| OOD + Drift                    |  0.9244 |  0.9539 |     0.5896 |      1      |   0.418  |        0.2086 |
| Uncertainty + Drift            |  0.866  |  0.9183 |     0.2937 |      1      |   0.1721 |        0.2614 |
| Original Fusion Baseline       |  0.9823 |  0.9899 |     0.9042 |      0.9902 |   0.832  |        0.1875 |