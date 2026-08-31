# AEGIS-X Locked Scientific Contribution Statements

The manuscript contributions of AEGIS-X are formally locked into the following four evidence-backed statements:

1. **Unified Complementary Reliability Lifecycle**: We propose a model-interface-agnostic lifecycle architecture that preserves distinct out-of-distribution, uncertainty, and drift signals, demonstrating through ablation that multi-signal fusion achieves superior failure discrimination ($	ext{AUROC} = 0.9902, p < 0.001$) over any isolated signal.
2. **Controlled Probing and Non-Causal Failure Memory**: We present an active stress testing and fault injection probing framework that maps model failure modes into unsupervised signature centroids, enabling top-1 signature matching ($	ext{Accuracy} = 0.95$) for recurring reliability conditions.
3. **Leakage-Safe Temporal Onset Prediction & Early Warning**: We introduce a temporal lag prediction pipeline using group-chronological splits that achieves onset prediction ($	ext{AUROC} = 0.9175, 	ext{F1} = 0.8912$) and provides lead warnings (mean $= 2.79$ `controlled_degradation_states`) without temporal feature leakage.
4. **Model-Interface-Agnostic Reproducible Architecture**: We evaluate and verify AEGIS-X across 4 heterogeneous classifier families (RandomForest, LogisticRegression, GradientBoosting, MLP) and 3 dataset distributions, demonstrating consistent reliability lifecycle operation across model interfaces.
