# Table 14: AEGIS-X Computational Overhead & Execution Latency

| Component                                     | Latency / Processing Time   | Resource           | Storage          |
|:----------------------------------------------|:----------------------------|:-------------------|:-----------------|
| Reference State Fit                           | 63.02 ms                    | Memory: ~45 MB     | Artifact: ~12 KB |
| Single-Sample Analysis (OOD+Unc+Drift+Fusion) | 0.023 ms / sample           | CPU Single-Core    | Result: ~2 KB    |
| Failure Memory Fitting (n=100 profiles)       | 14.20 ms                    | CPU Multi-Threaded | Memory: ~8 KB    |
| Temporal Failure Prediction Inference         | 1.85 ms / batch             | RAM: ~12 MB        | Model: ~150 KB   |