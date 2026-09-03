# AEGIS-X Module 14 Phase 5 — Pre-Registered Evaluation Protocol

## 1. Executive Summary & Provenance

This document establishes the pre-registered scientific evaluation protocol for Phase 5 of AEGIS-X Module 14: **Evidence-Calibrated Reliability Governance (ECRG)** / **Reliability Governor**.

All research questions, datasets, targets, horizons, baselines, ablations, metric equations, statistical analysis methods, and output formats are locked prior to accessing the internal final-test dataset or official external evaluation data.

- **Phase 5 Protocol Commit Target**: `chore(ecrg): preregister phase 5 evaluation protocol`
- **Starting Commit SHA**: `e98980c1d5c84e209676342b6dc7ba45ca98f903`
- **Data Firewall Lock**: Internal final-test engines (81–100) and official external test engines (100) are unopened prior to committing and pushing this protocol.

---

## 2. Locked Research Questions

1. **RQ1 — Conformal Validity & Efficiency**:
   Does ECRG achieve the pre-registered empirical marginal coverage $\ge 1-\alpha$ across static and temporal trajectories while maintaining compact, informative prediction sets?
   - *Primary metrics*: Empirical coverage, average set size, singleton set rate, ambiguous set rate $\{0,1\}$, empty set rate $\{\}$, calibration gap.

2. **RQ2 — Selective Governance Utility**:
   Does calibrated ECRG reduce unsafe automated continuation while maintaining high useful automation coverage?
   - *Primary metrics*: `CONTINUE` automation coverage, selective risk among `CONTINUE` decisions, unsafe continuation count/rate, review burden (`WATCH`/`DEFER`/`ESCALATE`), risk-coverage curve, and Area Under the Risk-Coverage Curve (AURCC).

3. **RQ3 — Temporal Warning Usefulness**:
   Does ECRG produce early warning lead prior to failure without excessive action instability or state flapping?
   - *Primary metrics*: First WATCH lead, first DEFER lead, first ESCALATE lead, missed warning rate, action transitions per 100 states, reversal/flapping rate, state dwell length, escalation frequency.

4. **RQ4 — Component Contribution (Ablation Study)**:
   What are the quantitative contributions of conformal calibration, separate evidence signals, fused risk scores, and the anti-flapping state machine?
   - *Primary metrics*: Paired difference in selective risk, coverage, and review burden across locked ablations A1–A4.

---

## 3. Datasets and Split Roles

### Primary Temporal Evaluation (Internal Final Test)
- **Dataset**: NASA C-MAPSS FD001 Genuine Trajectories
- **Training Cohort**: Engines 1–60 (60 trajectories, 12,431 cycle rows) — Used strictly for learner fitting and scaler reference parameters.
- **Calibration Cohort**: Engines 61–80 (20 trajectories, 4,353 cycle rows) — Used strictly for split conformal threshold $q$ calibration.
- **Primary Final-Test Cohort**: Engines 81–100 (20 trajectories) — **Unopened prior to protocol push**.

### External Validation Cohort
- **Dataset**: Official NASA C-MAPSS FD001 External Truncated Cohort (`test_FD001.txt` + `RUL_FD001.txt`, 100 test engines, 13,096 cycles).
- **Role**: External generalization check. Labelled explicitly as `Official NASA-provided simulated external truncated-RUL cohort`.

### Static Principal Evaluation
- **Datasets**: Breast Cancer Wisconsin & Digits Parity final-test splits.
- **Ground Truth**: `prediction_error = 1(y_pred != y_true)`.

---

## 4. Locked Target Semantics and Horizons

- **Supported Horizons**: $K \in \{1, 2, 3, 5\}$
- **Primary Target Semantic**: `C_MAPSS_RUL30_PROXY_WITHIN_K`
- **Secondary Target Semantics**: `C_MAPSS_RUL50_PROXY_WITHIN_K`, `C_MAPSS_TERMINAL_FAILURE_WITHIN_K`
- **Primary Nominal Risk**: $\alpha = 0.05$ (95% nominal coverage)
- **Sensitivity Levels**: $\alpha \in \{0.10, 0.20\}$

---

## 5. Locked Methods, Baselines & Ablations

### Evaluated Methods
1. `ECRG_CALIBRATED_FULL`: Full ECRG pipeline (Learner + Conformal Calibrator + State Machine).
2. `ECRG_EVIDENCE_ONLY`: Raw evidence signal contract output without conformal thresholding.
3. `UNCALIBRATED_RISK_LEARNER`: Logistic regression risk score without split conformal calibration.
4. `FROZEN_STRESS_ROBUST_FUSION`: Frozen Module 7 `StressRobustFusion` baseline.
5. `UNCERTAINTY_ONLY`: Single uncertainty score baseline.

### Preregistered Ablations
- **A1 — No Conformal Calibration**: Raw score thresholding without order-statistic quantile bounds.
- **A2 — Fused Evidence Only**: Excludes separate OOD, uncertainty, and drift scores.
- **A3 — Separate Signals Without Fused Risk**: Uses separate evidence components while excluding `fused_risk`.
- **A4 — No State Machine**: Instantaneous action mapping without anti-flapping hysteresis or cooldown.

---

## 6. Metric Definitions & Edge-Case Rules

1. **Automation Coverage**:
   $$\text{automation\_coverage} = \frac{\sum 1(\text{effective\_action} == \text{CONTINUE})}{N_{\text{total}}}$$

2. **Selective Risk**:
   $$\text{selective\_risk} = \frac{\sum 1(\text{effective\_action} == \text{CONTINUE} \land Y = 1)}{\sum 1(\text{effective\_action} == \text{CONTINUE})}$$

3. **Unsafe Continuation Rate**:
   $$\text{unsafe\_continuation\_rate} = \frac{\sum 1(\text{effective\_action} == \text{CONTINUE} \land Y = 1)}{N_{\text{total}}}$$

4. **Review Burden**:
   $$\text{review\_burden} = \frac{\sum 1(\text{effective\_action} \in \{\text{WATCH}, \text{DEFER}, \text{ESCALATE}\})}{N_{\text{total}}}$$

5. **Trajectory Coverage** (Primary Temporal Unit):
   $$\text{trajectory\_covered}(i) = 1 \iff \forall t \text{ eligible}, Y_{i,t} \in C_{\alpha}(X_{i,t})$$

6. **Edge-Case Rules**:
   - If denominator is zero: return `NA — undefined`. Never silently return 0.0.
   - External cohort zero positive outcome metrics: report `NA — no positive outcomes`.

---

## 7. Statistical Analysis & Bootstrap Specifications

- **Resampling Unit**: Trajectory/Engine-level cluster bootstrap for temporal datasets; sample-level bootstrap for static datasets.
- **Bootstrap Iterations**: 2,000 resamples (fixed seed = 42).
- **Exact Coverage Bounds**: Clopper-Pearson exact binomial confidence interval.
- **Multiple Comparisons**: Holm-Bonferroni correction applied across pre-registered baseline hypothesis tests. Both uncorrected and corrected $p$-values reported.

---

## 8. Expected Outputs and Artifact Manifest

Phase 5 will generate the following deterministic research artifacts under `aegis/governance/research_results/`:
- `phase5_protocol.json`
- `phase5_protocol.md`
- `phase5_results.json`
- `phase5_metrics.csv`
- `phase5_method_comparison.csv`
- `phase5_ablations.csv`
- `phase5_temporal_per_engine.csv`
- `phase5_statistical_tests.csv`
- `phase5_report.md`
- Figures: `fig1_risk_coverage.png`, `fig2_nominal_coverage.png`, `fig3_set_efficiency.png`, `fig4_action_distribution.png`, `fig5_warning_lead.png`, `fig6_ablation_effects.png`.
