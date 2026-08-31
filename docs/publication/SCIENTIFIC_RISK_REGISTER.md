# AEGIS-X Permanent Scientific Risk Register

| Risk ID   | Domain             | Description                                                                            | Status                                                             |
|:----------|:-------------------|:---------------------------------------------------------------------------------------|:-------------------------------------------------------------------|
| RISK-01   | OOD Evaluation     | Far-OOD synthetic separation is trivial; Near-OOD degrades to 0.7333.                  | MITIGATED (Near-OOD baseline reported explicitly)                  |
| RISK-02   | Failure Prediction | Temporal horizon is degradation states, NOT physical clock time.                       | MITIGATED (Horizon unit locked as controlled_degradation_states)   |
| RISK-03   | Failure Memory     | Signature clustering is associative, NOT causal root cause diagnosis.                  | MITIGATED (Explicit non-causal disclosures in UI & API)            |
| RISK-04   | External Validity  | Evaluated on 3 datasets; complex unstructured temporal tasks require V2 adapters.      | PARTIALLY_MITIGATED (Evaluated on Breast Cancer, Wine & Benchmark) |
| RISK-05   | Fusion Trade-Off   | StressRobust fusion tightens bounds under severe noise but raises floor in clean data. | MITIGATED (Detailed trade-off matrix in Table 6)                   |