# AEGIS-X Module 14 — Evidence-Calibrated Reliability Governance (ECRG)
## Scientific Contract & Governance Specification

**Status**: Approved Scientific Specification (Phase 1)  
**Target Branch**: `research/ecrg-module-14`  
**Reference Baseline Commit**: `0f7b48fa43e2c4a07d5acb05bbef06703c83c810`  

---

## A. Purpose & Non-Destructive Invariants

Module 14 — Evidence-Calibrated Reliability Governance (ECRG) translates reliability signals, anomaly signatures, and temporal hazard estimates from AEGIS-X Modules 1–13 into calibrated, action-oriented operational governance decisions.

### Strict Scientific Invariants
1. **Model Non-Interference**: ECRG operates strictly post-hoc / label-free on model outputs and reliability detectors. It must **never** retrain, overwrite, fine-tune, or redeploy the user's prediction model.
2. **Module 1–13 Immutability**: ECRG must not alter existing detector contracts or algorithms:
   - Out-of-Distribution (OOD) detector
   - Epistemic & Aleatoric Uncertainty quantifier
   - Feature Drift detector
   - Pre-label Risk Fusion (`StressRobustFusion`)
   - Synthetic Stress Testing Suite
   - Fault Injection Engine
   - Associative Failure Memory Bank
   - Temporal Failure Predictor
   - Early Warning Lead Unit (`controlled_degradation_states`)
   - C-MAPSS FD001–FD004 publication benchmarks

---

## B. Input Schema & Evidence Contract

The input contract strictly aggregates evidence produced by upstream Modules 1–13.

### Evidence Contract Fields

```python
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ECRGEvidenceContract(BaseModel):
    # Metadata & Identifiers (Always Required)
    model_id: str = Field(..., description="Target model identifier")
    dataset_id: str = Field(..., description="Evaluated dataset identifier")
    trajectory_id: Optional[str] = Field(None, description="Operational trajectory/unit ID")
    state_index: int = Field(..., ge=0, description="Sequential state step index within trajectory")
    timestamp: str = Field(..., description="ISO-8601 timestamp of evaluation state")
    source_analysis_id: Optional[str] = Field(None, description="Upstream analysis execution ID")
    
    # Label-Free Production Signals (Modules 1-4)
    ood_score: float = Field(..., ge=0.0, le=1.0, description="Module 1: Pre-label OOD risk score")
    uncertainty_score: float = Field(..., ge=0.0, le=1.0, description="Module 2: Predictive uncertainty score")
    drift_score: float = Field(..., ge=0.0, le=1.0, description="Module 3: Feature drift score")
    fused_risk: float = Field(..., ge=0.0, le=1.0, description="Module 4: StressRobustFusion risk score")
    
    # Detector Diagnostics & Interaction Signals
    signal_disagreement: float = Field(0.0, ge=0.0, le=1.0, description="Variance/disagreement across OOD, uncertainty, drift")
    ood_drift_redundancy: float = Field(0.0, ge=0.0, le=1.0, description="Covariance between OOD and Feature Drift signals")
    stress_robustness: float = Field(1.0, ge=0.0, le=1.0, description="Module 5: Evaluated model robustness factor")
    fault_sensitivity: float = Field(0.0, ge=0.0, le=1.0, description="Module 6: Evaluated fault sensitivity factor")
    
    # Advanced Intelligence Evidence (Modules 11-13)
    memory_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Module 11: Failure Memory k-NN similarity score")
    temporal_failure_probability: float = Field(0.0, ge=0.0, le=1.0, description="Module 12: Hazard model failure probability")
    early_warning_state: str = Field("NORMAL", description="Module 13: Degradation lead state (NORMAL/DEGRADED/CRITICAL)")
    prediction_horizon: int = Field(5, ge=1, description="Controlled degradation lead step horizon K")
    
    # Ground-Truth / Outcome Data (Labeled Calibration & Retrospective Evaluation ONLY)
    eventual_failure: Optional[bool] = Field(None, description="True trajectory outcome (None in production)")
    failure_within_horizon: Optional[bool] = Field(None, description="True failure within horizon K (None in production)")
```

### Label-Free vs. Labeled Field Demarcation

| Field Category | Label-Free Production | Labeled Calibration / Retrospective |
| :--- | :---: | :---: |
| Model & Dataset Metadata | **Available** | **Available** |
| OOD, Uncertainty, Drift, Fused Risk | **Available** | **Available** |
| Memory Similarity & Hazard Prob. | **Available** | **Available** |
| Early Warning Lead State | **Available** | **Available** |
| `eventual_failure` | **UNAVAILABLE** (None) | **Available** |
| `failure_within_horizon` | **UNAVAILABLE** (None) | **Available** |

---

## C. Operating Modes

ECRG strictly enforces two explicit operating modes:

### Mode 1: `EVIDENCE_ONLY`
- **Use Case**: Label-free production environments where target outcomes are absent.
- **Function**: Aggregates evidence, evaluates anti-flapping state transitions, reports risk drivers and non-causal evidence.
- **Outputs**: Current governance action (`CONTINUE`, `WATCH`, `DEFER`, `ESCALATE`), warning severity, supporting and contradictory evidence breakdown.
- **Statistical Claim**: Makes **no** formal conformal coverage or risk bounds claims.
- **Mandatory UI / Report Banner**:
  ```text
  LABEL-FREE / NON-CERTIFIED
  ```

### Mode 2: `CALIBRATED_GOVERNANCE`
- **Use Case**: Deployment environments with a strictly isolated labeled calibration dataset or verified delayed outcomes.
- **Function**: Fits split-conformal risk thresholds to guarantee a user-selected upper bound on unsafe automatic acceptance.
- **Outputs**: Calibrated quantile threshold $\hat{q}$, target risk $\alpha$, empirical calibration risk, empirical coverage, calibration set size $N_{cal}$, stated statistical assumptions, governance action.
- **Mandatory UI / Report Banner**:
  ```text
  CONFORMAL CALIBRATED (α = 0.05, N_cal = 120 trajectories)
  ```

---

## D. Governance Actions

ECRG emits exactly one of four discrete operational governance actions:

```text
CONTINUE | WATCH | DEFER | ESCALATE
```

### Action Semantics & Operational Definitions

1. **`CONTINUE`**: Evidence is within the validated safe operating boundary. The model's predictions may be processed automatically.
2. **`WATCH`**: Moderate degradation or early warning signals detected. Increase monitoring frequency, log telemetry, and issue soft alerts. Predictions continue automatically.
3. **`DEFER`**: Elevated risk or signal disagreement detected. Abstain from automatic prediction execution; route prediction to a human domain expert for manual verification.
4. **`ESCALATE`**: Severe degradation, high temporal failure probability, or critical early warning state reached. Trigger high-priority operational alert; initiate investigation for model recalibration, rollback, or retraining consideration.

*Constraint*: ECRG **never** automatically retrains, overwrites, or redeploys a user model.

---

## E. Formal Risk Boundary Specification

The conformal control objective is formulated around the risk of **unsafe automatic acceptance**:

$$\text{unsafe\_accept} = \begin{cases} 1 & \text{if } \text{action} == \text{CONTINUE} \text{ and } y_{H} == 1 \\ 0 & \text{otherwise} \end{cases}$$

where $y_{H}$ indicates a true failure occurring within the prediction horizon $H = K$ `controlled_degradation_states`.

### Mathematical Risk Bound
Given target risk $\alpha \in (0, 1)$ and calibration set $D_{cal} = \{(x_i, y_{i, H})\}_{i=1}^{N_{cal}}$:

$$R_{\text{unsafe}}(\hat{q}) = \mathbb{E}\left[ \mathbb{I}(S(x) \le \hat{q}) \cdot y_{H} \right] \le \alpha$$

Evaluated independently for degradation lead step horizons:

$$K \in \{1, 2, 3, 5\} \quad \text{controlled\_degradation\_states}$$

*Note*: Horizons represent discrete time-series steps $K$. Horizons are **not** converted into real-world clock time (seconds/minutes). The formal statistical guarantee applies strictly to the calibrated `CONTINUE` acceptance boundary.

---

## F. Dataset Splitting & Leakage Prevention Protocol

To guarantee zero data leakage and valid conformal calibration, datasets are partitioned according to a group-aware protocol:

```text
Training Set:     60%  (Used ONLY to train base hazard models / memory indices)
Calibration Set:  20%  (Used ONLY to compute conformal quantile threshold q_hat)
Final Test Set:   20%  (Used ONLY for final locked policy evaluation)
```

### Leakage Prevention Invariants
1. **Trajectory Grouping**: Partitioning is executed strictly by `trajectory_id` / unit ID. All states from a given trajectory belong exclusively to one split.
2. **Strict Threshold Isolation**: Conformal thresholds $\hat{q}$ are selected on Calibration data only. Thresholds are **never** tuned on Final Test data.
3. **Temporal Isolation**: Feature construction for state $t$ must never use information from state $t+k$ ($k > 0$).
4. **Preprocessing Isolation**: Scalers and transformations are fit exclusively on Training trajectory data and applied to Calibration and Test sets.

---

## G. Deterministic State-Machine Specification

To prevent alert flapping (rapid oscillations between governance states due to noise), ECRG incorporates a deterministic state machine:

```
                  +--------------------------------+
                  |           CONTINUE             |
                  +--------------------------------+
                     | (Risk > Tau_entry) | (Risk < Tau_exit for N_rec steps)
                     v                    |
                  +--------------------------------+
                  |            WATCH               |
                  +--------------------------------+
                     | (Risk > Tau_defer) | (Risk < Tau_exit for N_rec steps)
                     v                    |
                  +--------------------------------+
                  |            DEFER               |
                  +--------------------------------+
                     | (Risk > Tau_escalate OR EarlyWarning == CRITICAL)
                     v
                  +--------------------------------+
                  |           ESCALATE             | (Requires explicit reset/cooldown)
                  +--------------------------------+
```

### Anti-Flapping Parameters
- **`entry_threshold` ($\tau_{\text{entry}}$)**: Fused risk threshold to enter `WATCH`.
- **`defer_threshold` ($\tau_{\text{defer}}$)**: Fused risk / hazard threshold to enter `DEFER`.
- **`escalate_threshold` ($\tau_{\text{escalate}}$)**: Risk threshold to enter `ESCALATE`.
- **`min_consecutive_states` ($N_{\text{consec}}$)**: Minimum consecutive states above threshold required before transitioning to a higher severity state (default: 2 steps).
- **`cooldown_period` ($N_{\text{cooldown}}$)**: Minimum steps required in a state before de-escalation can occur (default: 3 steps).
- **`recovery_confirmation` ($N_{\text{rec}}$)**: Consecutive normal states required to de-escalate (default: 3 steps).
- **`escalation_persistence`**: Once `ESCALATE` is triggered, the state persists until an explicit administrative reset or complete trajectory reset.

---

## H. Evidence Attribution & Terminology

ECRG provides non-causal decision evidence to explain every governance decision.

### Approved Terminology
- **Supporting Evidence**: Reliability detectors whose risk score exceeds $\tau_{\text{entry}}$.
- **Contradictory Evidence**: Reliability detectors whose risk score remains low while other signals report high risk.
- **Signal Disagreement**: Variance across OOD, Uncertainty, and Drift detectors.
- **Historical Association**: Memory similarity to previously stored failure signatures.

### Forbidden Terminology
- Do **NOT** use "Causal root cause".
- Do **NOT** use "Proven cause".
- Do **NOT** use "Guaranteed prevention".

---

## I. Policy Replay Simulator

The offline Policy Replay Simulator evaluates how historical held-out test trajectories would have performed under different governance policies.

### Simulator Inputs
- Target Risk $\alpha$
- Target Coverage
- Warning / Defer / Escalate Thresholds
- Anti-flapping parameters ($N_{\text{consec}}$, $N_{\text{cooldown}}$)
- Cost Matrix:
  - False-Warning Cost ($C_{fw}$)
  - Missed-Failure Cost ($C_{mf}$)
  - Deferral Cost ($C_{def}$)

### Simulator Outputs
- Empirical Coverage & Selective Risk
- Abstention Rate & Failure Capture Rate
- Missed-Failure Rate & False-Warning Rate
- Mean / Median Warning Lead Steps
- Intervention Frequency & State Transition Count
- Total Estimated Operational Cost

---

## J. Locked Baselines & Ablations (10 Comparisons)

1. **Best Individual Signal**: Max single detector (OOD / Drift / Uncertainty).
2. **Original Weighted Fusion**: Standard linear combination of signals.
3. **`StressRobustFusion`**: Module 4 adversarial risk fusion.
4. **Fixed Thresholding**: Static fused risk cutoff.
5. **Temporal Predictor Only**: Module 12 sequence hazard output only.
6. **Conformal Calibration Only**: Conformal risk control without state-machine anti-flapping.
7. **ECRG w/o Failure Memory**: ECRG pipeline excluding Module 11 memory similarity.
8. **ECRG w/o Temporal Evidence**: ECRG pipeline excluding Module 12/13 temporal hazard signals.
9. **ECRG w/o Anti-Flapping**: Raw threshold transitions without consecutive step/cooldown rules.
10. **Complete ECRG**: Full calibrated governance pipeline.

---

## K. Locked Evaluation Metrics (17 Metrics)

1. **AUROC**: Area Under ROC Curve
2. **AUPRC**: Area Under Precision-Recall Curve
3. **Brier Score**: Probability calibration accuracy
4. **ECE**: Expected Calibration Error
5. **Coverage**: Proportion of predictions automatically accepted (`CONTINUE`)
6. **Selective Risk**: Failure rate among accepted predictions
7. **Risk–Coverage Curve**: Selective risk plotted against coverage
8. **AURCC**: Area Under Risk–Coverage Curve
9. **Abstention Rate**: Proportion of `DEFER` + `ESCALATE` actions
10. **Failure Capture Rate**: Proportion of true failures preceded by `WATCH`, `DEFER`, or `ESCALATE`
11. **False-Warning Rate**: Proportion of normal states assigned `WATCH`/`DEFER`/`ESCALATE`
12. **Missed-Failure Rate**: Proportion of true failures accepted as `CONTINUE`
13. **Mean Warning Lead**: Average step lead time before failure
14. **Median Warning Lead**: Median step lead time before failure
15. **State-Transition Count**: Total governance state changes (flapping frequency)
16. **Runtime Overhead**: Processing time per state evaluation (milliseconds)
17. **Bootstrap 95% CI**: Multi-seed bootstrap confidence intervals ($N=1000$)

---

## L. Acceptance Gates for Phase 2+ Integration

Module 14 implementation may proceed to integration only when:
1. Zero data leakage across trajectory splits is verified by unit tests.
2. Training, Calibration, and Test splits are strictly independent.
3. Results reproduce 100% cleanly from a single execution script.
4. Runtime overhead remains $< 50\text{ms}$ per state evaluation.
5. All 10 baselines and ablations run successfully.
6. Negative/domain-dependent results are preserved and reported honestly.
7. `EVIDENCE_ONLY` mode displays `LABEL-FREE / NON-CERTIFIED`.
8. `CALIBRATED_GOVERNANCE` states all statistical assumptions explicitly.
9. Modules 1–13 code and results remain untouched.
10. Production deployment remains unaffected.
